"""Pseudo-log-likelihood of sentences under a masked LM: a batched version of minicons' scorer.

Same quantity as minicons' MaskedLMScorer.sequence_score with PLL_metric="within_word_l2r" and a sum
reduction (Kauf & Ivanova, 2023): every token of the sentence is predicted in turn with itself and the
following tokens of the same word masked, and the log-probabilities are summed. minicons projects every
position of every masked copy onto the vocabulary; here only the masked target position goes through the
output head, and copies from different sentences are batched together by length, which is about ten
times faster on a CPU. --selftest compares the two implementations.

    from pll import PLLScorer
    scores = PLLScorer("tahrirchi/tahrirchi-bert-base").score(["Hech kim kelmadi.", "Hech kim keldi."])

    python scripts/pll.py --selftest --model tahrirchi/tahrirchi-bert-base
"""
import argparse
import csv
import sys
from pathlib import Path

import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent


class PLLScorer:
    def __init__(self, model_name, device="cpu", dtype=torch.float32):
        self.tok = AutoTokenizer.from_pretrained(model_name)
        try:
            self.model = AutoModelForMaskedLM.from_pretrained(model_name, dtype=dtype)
        except TypeError:  # transformers before 4.56 calls it torch_dtype
            self.model = AutoModelForMaskedLM.from_pretrained(model_name, torch_dtype=dtype)
        self.model.to(device).eval()
        self.device = device
        # The output head (hidden state -> vocabulary logits): `cls` in BERT, `lm_head` in RoBERTa and XLM-R.
        self.head = next((getattr(self.model, n) for n in ("cls", "lm_head") if hasattr(self.model, n)), None)
        self.encoder = self.model.base_model if self.head is not None else None
        self.special = {self.tok.pad_token_id, self.tok.cls_token_id, self.tok.sep_token_id}

    def copies(self, sentence):
        """The masked copies of one sentence: (token ids with masks, position of the target, id of the target)."""
        enc = self.tok(sentence)
        ids, words = enc["input_ids"], enc.word_ids()
        targets = [i for i, t in enumerate(ids) if t not in self.special]
        out = []
        for pos in targets:
            masked = list(ids)
            masked[pos] = self.tok.mask_token_id
            if words[pos] is not None:  # also mask the rest of the word, as in within_word_l2r
                for j in range(pos + 1, targets[-1] + 1):
                    if words[j] == words[pos]:
                        masked[j] = self.tok.mask_token_id
            out.append((masked, pos, ids[pos]))
        return out

    @torch.no_grad()
    def score(self, sentences, batch_size=128, progress=None):
        """Summed pseudo-log-likelihood (natural log) of each sentence."""
        rows = [(s, *c) for s, sent in enumerate(sentences) for c in self.copies(sent)]
        order = sorted(range(len(rows)), key=lambda k: len(rows[k][1]))  # similar lengths per batch
        scores = [0.0] * len(sentences)
        pad = self.tok.pad_token_id
        for start in range(0, len(order), batch_size):
            batch = [rows[k] for k in order[start:start + batch_size]]
            width = max(len(r[1]) for r in batch)
            x = torch.tensor([r[1] + [pad] * (width - len(r[1])) for r in batch], device=self.device)
            mask = torch.tensor([[1] * len(r[1]) + [0] * (width - len(r[1])) for r in batch], device=self.device)
            pos = torch.tensor([r[2] for r in batch], device=self.device)
            rng = torch.arange(len(batch), device=self.device)
            if self.head is not None:
                hidden = self.encoder(input_ids=x, attention_mask=mask).last_hidden_state
                logits = self.head(hidden[rng, pos])
            else:
                logits = self.model(input_ids=x, attention_mask=mask).logits[rng, pos]
            logp = torch.log_softmax(logits.float(), dim=-1)
            for (s, _, _, target), value in zip(batch, logp[rng, torch.tensor([r[3] for r in batch], device=self.device)].tolist()):
                scores[s] += value
            if progress:
                progress(min(start + batch_size, len(order)), len(order))
        return scores


def selftest(model_name, n):
    """Compare with minicons on n benchmark sentences in Latin and Cyrillic; returns the number of failures."""
    from minicons import scorer

    sents = []
    for name in ("uzblimp.tsv", "uzblimp_cyrl.tsv"):
        with open(ROOT / "data" / "benchmark" / name, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
        step = max(1, len(rows) // (n // 4))
        sents += [r[k] for r in rows[::step][:n // 4] for k in ("grammatical", "ungrammatical")]
    fast = PLLScorer(model_name).score(sents)
    lm = scorer.MaskedLMScorer(model_name, device="cpu", dtype=torch.float32)
    if not hasattr(lm.tokenizer, "batch_encode_plus"):
        lm.tokenizer.batch_encode_plus = lambda texts, **kw: lm.tokenizer(texts, **kw)
    slow = []
    for i in range(0, len(sents), 8):
        slow += lm.sequence_score(sents[i:i + 8], reduction=lambda x: x.sum(0).item(), PLL_metric="within_word_l2r")
    worst = max(abs(a - b) for a, b in zip(fast, slow))
    flips = sum((fast[i] > fast[i + 1]) != (slow[i] > slow[i + 1]) for i in range(0, len(sents), 2))
    print(f"{model_name}: {len(sents)} sentences, largest difference {worst:.2e} nats, {flips} pairs judged differently")
    return int(worst > 1e-3 or flips > 0)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--selftest", action="store_true", help="compare with minicons on a sample of benchmark sentences")
    p.add_argument("--model", default="tahrirchi/tahrirchi-bert-base")
    p.add_argument("--n", type=int, default=80, help="number of sentences in the comparison")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.selftest:
        sys.exit(selftest(args.model, args.n))
    p.error("nothing to do: import PLLScorer, or run with --selftest")

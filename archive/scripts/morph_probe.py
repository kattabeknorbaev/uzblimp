"""Run TurkicNLP's Uzbek morphology on a few sentences and print every analysis.

For each word: UPOS, lemma and UD features from the Glot500 neural analyser
(morph_neural), plus labeled segments from the MorphemeTokenizer. The output is
for checking by hand whether case and negation are tagged reliably.

Corpus sentences come from data/candidates/ (local only); the output contains
corpus text, so don't commit it.

    set TURKICNLP_MODELS_DIR=D:/turkicnlp_models
    python scripts/morph_probe.py --take keyin_ablative:4 hech_negated_verb:3 numeral_ta_noun:3
    python scripts/morph_probe.py --sentences "Hech kim kelmadi." "Uchta kitob oldim."
"""
import argparse
import csv
import sys
from pathlib import Path

import turkicnlp
import turkicnlp.processors.multilingual_morph_model as morph_model
from turkicnlp.processors.morpheme_tokenizer import MorphemeTokenizer
from turkicnlp.resources.registry import ModelRegistry

# Workaround (turkicnlp 0.4.0): the downloader saves Glot500 as a plain folder
# (snapshot_download(local_dir=...)), but the model loads it by repo name with
# cache_dir=..., which expects the HF cache layout and so downloads 1.6 GB again.
# Point the loader at the folder that is already there.
_local_backbone = ModelRegistry.default_dir() / "huggingface" / "cis-lmu--glot500-base"
if (_local_backbone / "model.safetensors").exists():
    morph_model.BACKBONE_NAME = str(_local_backbone)


def load_candidates(cand_dir, takes):
    out = []
    for spec in takes:
        name, n = spec.split(":")
        with open(Path(cand_dir) / f"{name}.tsv", encoding="utf-8") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))[: int(n)]
        out += [(name, r["sentence"]) for r in rows]
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cand-dir", default="data/candidates")
    p.add_argument("--take", nargs="*", default=[], help="file:N pairs, e.g. keyin_ablative:4")
    p.add_argument("--sentences", nargs="*", default=[], help="extra sentences to analyse")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    items = load_candidates(args.cand_dir, args.take) + [("own", s) for s in args.sentences]
    # Rule-based tokenizer: the default for uzb is the custom Stanza one (needs [stanza]).
    nlp = turkicnlp.Pipeline("uzb", processors=["tokenize", "morph_neural"], tokenize_backend="rule")
    seg = MorphemeTokenizer(lang="uzb")
    seg.load()

    for i, (source, text) in enumerate(items, 1):
        print(f"\n[{i}] ({source}) {text}")
        for sent in nlp(text).sentences:
            for w in sent.words:
                if w.upos == "PUNCT":
                    continue
                labeled = seg.segment(w.text).labeled
                segs = "+".join(f"{m}/{lab}" for m, lab in labeled)
                print(f"    {w.text:18} {w.upos or '_':6} {w.lemma or '_':14} {w.feats or '_':55} {segs}")


if __name__ == "__main__":
    main()

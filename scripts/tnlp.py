"""Thin wrapper around TurkicNLP (0.4.0) for UzBLiMP; see notes/turkicnlp.md.

Uses only the parts that tested reliable for Uzbek: the MorphemeTokenizer's
case/negation labels (ABL 6/7, NEG 5/5) and UPOS from the Glot500 analyser.
Models load lazily from TURKICNLP_MODELS_DIR (default D:/turkicnlp_models).
"""
import os
from functools import lru_cache

os.environ.setdefault("TURKICNLP_MODELS_DIR", "D:/turkicnlp_models")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import turkicnlp  # noqa: E402
import turkicnlp.processors.multilingual_morph_model as _morph_model  # noqa: E402
from turkicnlp.processors.morpheme_tokenizer import MorphemeTokenizer  # noqa: E402
from turkicnlp.resources.registry import ModelRegistry  # noqa: E402

# Workaround: the downloader stores Glot500 as a plain folder, but the model loads
# it by repo name with cache_dir=..., which would download 1.6 GB again.
_local_backbone = ModelRegistry.default_dir() / "huggingface" / "cis-lmu--glot500-base"
if (_local_backbone / "model.safetensors").exists():
    _morph_model.BACKBONE_NAME = str(_local_backbone)


class Analyzer:
    def __init__(self):
        self._seg = None
        self._nlp = None

    @lru_cache(maxsize=100_000)
    def labels(self, word):
        """Morpheme labels of one word, e.g. ['STEM', 'POSS.1SG', 'ABL']."""
        if self._seg is None:
            self._seg = MorphemeTokenizer(lang="uzb")
            self._seg.load()
        return [lab for _, lab in self._seg.segment(word).labeled]

    @lru_cache(maxsize=20_000)
    def upos(self, sentence):
        """[(token, UPOS)] for one sentence (rule tokenizer + Glot500 morph)."""
        if self._nlp is None:
            self._nlp = turkicnlp.Pipeline("uzb", processors=["tokenize", "morph_neural"],
                                           tokenize_backend="rule")
        return tuple((w.text, w.upos) for s in self._nlp(sentence).sentences for w in s.words)

    def upos_of(self, sentence, word):
        return next((u for t, u in self.upos(sentence) if t == word), None)

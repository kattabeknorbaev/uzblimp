"""The models evaluated on UzBLiMP: one registry for the runner, the report, the tables and the figures.

Each entry gives the Hugging Face id, how the model is scored and what the paper says about it.
Per-pair results of a run live in results/<last part of the id>_uzblimp_<version><suffix>.csv, where the
suffix names the alphabet ("" current Latin, "_cyrl" Cyrillic, "_reformed" reformed Latin); the four
models scored before this registry existed keep their file names (see LEGACY_STEMS).

    from models import MODELS, load_runs
    runs = load_runs()              # {(key, alphabet): DataFrame indexed by pair id}
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
# Benchmark version the result files refer to. v1.2 = v1.1 with corrected Cyrillic spelling of Russian
# loanwords in 41 pairs; current Latin and reformed Latin are unchanged.
VERSION = "v1.2"
ALPHABETS = {"Latin": "", "Cyrillic": "_cyrl", "Reformed": "_reformed"}
DATA = {"Latin": "uzblimp.tsv", "Cyrillic": "uzblimp_cyrl.tsv", "Reformed": "uzblimp_reformed.tsv"}
RELEASE_SCRIPT = {"Latin": "latn", "Cyrillic": "cyrl", "Reformed": "latn_reformed"}

# key        short name used in tables and figures
# hf         Hugging Face id
# method     "logprob" (causal LM, summed token log-probabilities) or "pll" (masked LM, pseudo-log-likelihood)
# group      table section
# trained    script of the Uzbek text the model was trained on: latn, cyrl, both (multilingual models: what
#            their Uzbek data is believed to contain), or none
# params     number of parameters, as given by the model's authors or card
# size       Goldfish only: training-data size label
MODELS = [
    # Monolingual causal LMs: the Goldfish data-size ladder in each script (Chang et al., 2024)
    dict(key="GF-L 5MB", hf="goldfish-models/uzn_latn_5mb", params="39M", method="logprob", group="Goldfish (Latin)", trained="latn", size="5MB"),
    dict(key="GF-L 10MB", hf="goldfish-models/uzn_latn_10mb", params="39M", method="logprob", group="Goldfish (Latin)", trained="latn", size="10MB"),
    dict(key="GF-L 100MB", hf="goldfish-models/uzn_latn_100mb", params="125M", method="logprob", group="Goldfish (Latin)", trained="latn", size="100MB"),
    dict(key="GF-L full", hf="goldfish-models/uzn_latn_full", params="125M", method="logprob", group="Goldfish (Latin)", trained="latn", size="full"),
    dict(key="GF-C 5MB", hf="goldfish-models/uzn_cyrl_5mb", params="39M", method="logprob", group="Goldfish (Cyrillic)", trained="cyrl", size="5MB"),
    dict(key="GF-C 10MB", hf="goldfish-models/uzn_cyrl_10mb", params="39M", method="logprob", group="Goldfish (Cyrillic)", trained="cyrl", size="10MB"),
    dict(key="GF-C 100MB", hf="goldfish-models/uzn_cyrl_100mb", params="125M", method="logprob", group="Goldfish (Cyrillic)", trained="cyrl", size="100MB"),
    dict(key="GF-C full", hf="goldfish-models/uzn_cyrl_full", params="125M", method="logprob", group="Goldfish (Cyrillic)", trained="cyrl", size="full"),
    # Uzbek masked LMs
    dict(key="tahrirchi-bert", hf="tahrirchi/tahrirchi-bert-base", params="110M", method="pll", group="Uzbek encoders", trained="latn"),
    dict(key="tahrirchi-bert-small", hf="tahrirchi/tahrirchi-bert-small", params="67M", method="pll", group="Uzbek encoders", trained="latn"),
    dict(key="BERTbek", hf="elmurod1202/bertbek-news-big-cased", params="110M", method="pll", group="Uzbek encoders", trained="latn"),
    dict(key="UzBERT", hf="coppercitylabs/uzbert-base-uncased", params="110M", method="pll", group="Uzbek encoders", trained="cyrl"),
    dict(key="UzRoBERTa", hf="rifkat/uztext-3Gb-BPE-Roberta", params="84M", method="pll", group="Uzbek encoders", trained="both"),
    # Multilingual masked LMs
    dict(key="mBERT", hf="google-bert/bert-base-multilingual-cased", params="179M", method="pll", group="Multilingual encoders", trained="multi"),
    dict(key="XLM-R base", hf="FacebookAI/xlm-roberta-base", params="279M", method="pll", group="Multilingual encoders", trained="multi"),
    dict(key="Glot500", hf="cis-lmu/glot500-base", params="395M", method="pll", group="Multilingual encoders", trained="multi"),
    dict(key="XLM-R large", hf="FacebookAI/xlm-roberta-large", params="561M", method="pll", group="Multilingual encoders", trained="multi"),
    # Multilingual causal LMs
    dict(key="Qwen2.5-0.5B", hf="Qwen/Qwen2.5-0.5B", params="0.5B", method="logprob", group="Multilingual LMs", trained="multi"),
    dict(key="Qwen2.5-1.5B", hf="Qwen/Qwen2.5-1.5B", params="1.5B", method="logprob", group="Multilingual LMs", trained="multi"),
    dict(key="mGPT", hf="ai-forever/mGPT", params="1.3B", method="logprob", group="Multilingual LMs", trained="multi"),
    dict(key="mGPT-Uzbek", hf="ai-forever/mGPT-1.3B-uzbek", params="1.3B", method="logprob", group="Multilingual LMs", trained="multi"),
]

# File stems of the four runs made with score_pairs.py before the registry ({v} = version).
LEGACY_STEMS = {
    ("Qwen/Qwen2.5-0.5B", "Latin"): "Qwen2.5-0.5B_uzblimp_{v}_bos",
    ("Qwen/Qwen2.5-0.5B", "Cyrillic"): "Qwen2.5-0.5B_uzblimp_{v}_cyrl_bos",
    ("Qwen/Qwen2.5-0.5B", "Reformed"): "Qwen2.5-0.5B_uzblimp_{v}_reformed_bos",
}


def by_key(key):
    return next(m for m in MODELS if m["key"] == key)


def stem(model, alphabet, version):
    """File stem (no folder, no .csv) of a run's per-pair results."""
    legacy = LEGACY_STEMS.get((model["hf"], alphabet))
    if legacy:
        return legacy.format(v=version)
    return f"{model['hf'].split('/')[-1]}_uzblimp_{version}{ALPHABETS[alphabet]}"


def csv_path(model, alphabet, version):
    return ROOT / "results" / f"{stem(model, alphabet, version)}.csv"


def load_runs(version=VERSION, keys=None):
    """{(key, alphabet): per-pair DataFrame indexed by pair id} for every run that has been scored."""
    runs = {}
    for m in MODELS:
        if keys and m["key"] not in keys:
            continue
        for alphabet in ALPHABETS:
            f = csv_path(m, alphabet, version)
            if f.exists():
                runs[(m["key"], alphabet)] = pd.read_csv(f).set_index("id")
    return runs

"""The models evaluated on UzBLiMP: one registry for the runner, the report, the tables and the figures.

Each entry gives the Hugging Face id, how the model is scored and what the paper says about it.
Per-pair results of a run on the current benchmark version live in results/lm/<alphabet>/<model>.csv, where
<alphabet> is latn, cyrl or latn_reformed and <model> is the last part of the Hugging Face id in lower case.
Results of earlier versions are kept in archive/results/ under their old names, <last part of the
id>_uzblimp_<version><suffix>.csv with the suffix "" (current Latin), "_cyrl" or "_reformed" (see stem and
LEGACY_STEMS).

    from models import MODELS, load_runs
    runs = load_runs()              # {(key, alphabet): DataFrame indexed by pair id}
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
# Benchmark version the result files refer to. v1.2 = v1.1 with the Cyrillic spelling of Russian loanwords
# corrected and with 120 pairs replaced from the reserve after an audit and two spelling passes (data/benchmark/excluded.tsv).
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
# name       name printed in the paper where it differs from the key
# params     number of parameters, as given by the model's authors or card
# size       Goldfish only: training-data size label
# license    as given on the model's Hugging Face page (checked 2026-11-22 and 2026-11-24)
# setup      "gpu" for the larger models scored on rented GPUs for the second author (results/lm/gpu_runs/README.txt;
#            imported by archive/scripts/import_gpu_runs.py); all other models were scored on CPU in float32
# dtype      precision of a GPU run; post: True for post-trained (not base) checkpoints, scored like the others
# held_out   False for Tomaris.ai, whose pretraining corpus contains most benchmark sentences of the authors' own
#            corpus and which was made by the authors' company (results/lm/gpu_runs/tomaris_overlap_v1.2.json)
# device     "gpu" for the models of the CPU groups that were scored with run_models.py (the same scorer, float32)
#            on a rented GPU in run 3 of the GPU runs (results/lm/gpu_runs/README_run3.txt)
# record     the README of the GPU run in results/lm/gpu_runs/ (default README.txt, runs 1 and 2)
# invalid    alphabets whose run is not reported, with the reason (the per-pair file is kept in results/lm/gpu_runs/invalid)
MODELS = [
    # Monolingual causal LMs: the Goldfish data-size ladder in each script (Chang et al., 2024)
    dict(key="GF-L 5MB", hf="goldfish-models/uzn_latn_5mb", params="39M", method="logprob", group="Goldfish (Latin)", trained="latn", size="5MB", license="Apache 2.0"),
    dict(key="GF-L 10MB", hf="goldfish-models/uzn_latn_10mb", params="39M", method="logprob", group="Goldfish (Latin)", trained="latn", size="10MB", license="Apache 2.0"),
    dict(key="GF-L 100MB", hf="goldfish-models/uzn_latn_100mb", params="125M", method="logprob", group="Goldfish (Latin)", trained="latn", size="100MB", license="Apache 2.0"),
    dict(key="GF-L full", hf="goldfish-models/uzn_latn_full", params="125M", method="logprob", group="Goldfish (Latin)", trained="latn", size="full", license="Apache 2.0"),
    dict(key="GF-C 5MB", hf="goldfish-models/uzn_cyrl_5mb", params="39M", method="logprob", group="Goldfish (Cyrillic)", trained="cyrl", size="5MB", license="Apache 2.0"),
    dict(key="GF-C 10MB", hf="goldfish-models/uzn_cyrl_10mb", params="39M", method="logprob", group="Goldfish (Cyrillic)", trained="cyrl", size="10MB", license="Apache 2.0"),
    dict(key="GF-C 100MB", hf="goldfish-models/uzn_cyrl_100mb", params="125M", method="logprob", group="Goldfish (Cyrillic)", trained="cyrl", size="100MB", license="Apache 2.0"),
    dict(key="GF-C full", hf="goldfish-models/uzn_cyrl_full", params="125M", method="logprob", group="Goldfish (Cyrillic)", trained="cyrl", size="full", license="Apache 2.0"),
    # Uzbek masked LMs
    dict(key="tahrirchi-bert", name="TahrirchiBERT", hf="tahrirchi/tahrirchi-bert-base", params="110M", method="pll", group="Uzbek encoders", trained="latn", license="Apache 2.0"),
    dict(key="tahrirchi-bert-small", name="TahrirchiBERT-small", hf="tahrirchi/tahrirchi-bert-small", params="67M", method="pll", group="Uzbek encoders", trained="latn", license="Apache 2.0"),
    dict(key="BERTbek", hf="elmurod1202/bertbek-news-big-cased", params="110M", method="pll", group="Uzbek encoders", trained="latn", license="MIT"),
    dict(key="UzBERT", hf="coppercitylabs/uzbert-base-uncased", params="110M", method="pll", group="Uzbek encoders", trained="cyrl", license="MIT"),
    dict(key="UzRoBERTa", hf="rifkat/uztext-3Gb-BPE-Roberta", params="84M", method="pll", group="Uzbek encoders", trained="both", license="Apache 2.0"),
    # Multilingual masked LMs
    dict(key="mBERT", hf="google-bert/bert-base-multilingual-cased", params="179M", method="pll", group="Multilingual encoders", trained="multi", license="Apache 2.0"),
    dict(key="XLM-R base", hf="FacebookAI/xlm-roberta-base", params="279M", method="pll", group="Multilingual encoders", trained="multi", license="MIT"),
    dict(key="Glot500", hf="cis-lmu/glot500-base", params="395M", method="pll", group="Multilingual encoders", trained="multi", license="Apache 2.0", device="gpu"),
    dict(key="XLM-R large", hf="FacebookAI/xlm-roberta-large", params="561M", method="pll", group="Multilingual encoders", trained="multi", license="MIT", device="gpu"),
    # Multilingual causal LMs
    dict(key="Qwen2.5-0.5B", hf="Qwen/Qwen2.5-0.5B", params="0.5B", method="logprob", group="Multilingual LMs", trained="multi", license="Apache 2.0"),
    dict(key="Qwen2.5-1.5B", hf="Qwen/Qwen2.5-1.5B", params="1.5B", method="logprob", group="Multilingual LMs", trained="multi", license="Apache 2.0"),
    dict(key="mGPT", hf="ai-forever/mGPT", params="1.3B", method="logprob", group="Multilingual LMs", trained="multi", license="Apache 2.0", device="gpu"),
    dict(key="mGPT-Uzbek", hf="ai-forever/mGPT-1.3B-uzbek", params="1.3B", method="logprob", group="Multilingual LMs", trained="multi", license="MIT", device="gpu"),
    # Larger causal LMs, scored on GPUs (see setup above)
    dict(key="Qwen3.5-0.8B", hf="Qwen/Qwen3.5-0.8B-Base", params="0.9B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="float32", post=False),
    dict(key="Qwen3.5-2B", hf="Qwen/Qwen3.5-2B-Base", params="2.3B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="float32", post=False),
    dict(key="Qwen3.5-4B", hf="Qwen/Qwen3.5-4B-Base", params="4.7B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="float32", post=False),
    dict(key="Qwen3.5-9B", hf="Qwen/Qwen3.5-9B-Base", params="9.7B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="float32", post=False),
    dict(key="Gemma 4 E4B", hf="google/gemma-4-E4B", params="8.0B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="float32", post=False),
    dict(key="Llama 3.1 8B", hf="unsloth/Meta-Llama-3.1-8B", params="8.0B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Llama 3.1 Community License", setup="gpu", dtype="float32", post=False),
    dict(key="Mistral Small 3.1", hf="mistralai/Mistral-Small-3.1-24B-Base-2503", params="24.0B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="bfloat16", post=False),
    dict(key="Gemma 4 26B-A4B", hf="google/gemma-4-26B-A4B", params="25.8B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="bfloat16", post=False),
    dict(key="Gemma 4 31B", hf="google/gemma-4-31B", params="31.3B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="bfloat16", post=False),
    dict(key="Qwen3.5-27B", hf="Qwen/Qwen3.5-27B", params="27.8B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="bfloat16", post=True),
    dict(key="Qwen3.6-27B", hf="Qwen/Qwen3.6-27B", params="27.8B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="bfloat16", post=True),
    dict(key="Qwen3.8-27B", hf="Qwen/Qwen3.8-27B", params="27.8B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="bfloat16", post=True),
    dict(key="Qwen3.5-35B-A3B", hf="Qwen/Qwen3.5-35B-A3B-Base", params="36.0B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="bfloat16", post=False),
    dict(key="Qwen3.6-35B-A3B", hf="Qwen/Qwen3.6-35B-A3B", params="36.0B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="bfloat16", post=True),
    # Scored on GPUs in run 3 (results/lm/gpu_runs/README_run3.txt): further multilingual LMs, then fine-tunes of
    # multilingual models for Uzbek or Kazakh. alloma 8B was fine-tuned from Llama-3.1-8B-Instruct (its model card).
    dict(key="Gemma 3 4B", hf="google/gemma-3-4b-pt", params="4.3B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Gemma Terms of Use", setup="gpu", dtype="float32", post=False, record="README_run3.txt"),
    dict(key="Gemma 3 12B", hf="google/gemma-3-12b-pt", params="12.2B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Gemma Terms of Use", setup="gpu", dtype="bfloat16", post=False, record="README_run3.txt"),
    dict(key="Gemma 3 27B", hf="google/gemma-3-27b-pt", params="27.4B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="Gemma Terms of Use", setup="gpu", dtype="bfloat16", post=False, record="README_run3.txt"),
    dict(key="Aya Expanse 8B", hf="CohereLabs/aya-expanse-8b", params="8.0B", method="logprob", group="Larger multilingual LMs (GPU)", trained="multi", license="CC BY-NC 4.0", setup="gpu", dtype="float32", post=True, record="README_run3.txt"),
    dict(key="alloma 8B", hf="uzlm/alloma-8B-Base", params="8.0B", method="logprob", group="Fine-tuned for Uzbek or Kazakh (GPU)", trained="multi", license="Llama 3.2 Community License", setup="gpu", dtype="float32", post=True, record="README_run3.txt",
         invalid={"Cyrillic": "its tokenizer deletes Cyrillic letters, so 2,297 of the 2,400 Cyrillic pairs tie"}),
    dict(key="Llama 3.1 8B Uz", hf="behbudiy/Llama-3.1-8B-Instruct-Uz", params="8.0B", method="logprob", group="Fine-tuned for Uzbek or Kazakh (GPU)", trained="multi", license="Llama 3.1 Community License", setup="gpu", dtype="float32", post=True, record="README_run3.txt"),
    dict(key="NeuronAI-Uzbek", hf="NeuronUz/NeuronAI-Uzbek", params="4.1B", method="logprob", group="Fine-tuned for Uzbek or Kazakh (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="float32", post=True, record="README_run3.txt"),
    dict(key="Qwen3.5-9B Kazakh", hf="issai/Qwen3.5-9B-Base-Kazakh", params="9.1B", method="logprob", group="Fine-tuned for Uzbek or Kazakh (GPU)", trained="multi", license="Apache 2.0", setup="gpu", dtype="float32", post=False, record="README_run3.txt"),
    # The authors' company's model: reported in the appendix only, as not held out (see held_out above)
    dict(key="Tomaris.ai", hf="tomaris/Tomaris.ai", params="27.1B", method="logprob", group="Not held out (authors' company)", trained="multi", license="none stated", setup="gpu", dtype="bfloat16", post=True, held_out=False),
]

# Old file stems of the runs made with score_pairs.py before the registry ({v} = version).
LEGACY_STEMS = {
    ("Qwen/Qwen2.5-0.5B", "Latin"): "Qwen2.5-0.5B_uzblimp_{v}_bos",
    ("Qwen/Qwen2.5-0.5B", "Cyrillic"): "Qwen2.5-0.5B_uzblimp_{v}_cyrl_bos",
    ("Qwen/Qwen2.5-0.5B", "Reformed"): "Qwen2.5-0.5B_uzblimp_{v}_reformed_bos",
}


def by_key(key):
    return next(m for m in MODELS if m["key"] == key)


def label(model):
    """Name of a model (registry entry or key) as printed in the paper."""
    model = by_key(model) if isinstance(model, str) else model
    return model.get("name", model["key"])


def stem(model, alphabet, version):
    """Old-style file stem (no folder, no .csv) of a run's per-pair results: the name of an earlier version's
    file in archive/results/, and the dataset name of a run in the run log."""
    legacy = LEGACY_STEMS.get((model["hf"], alphabet))
    if legacy:
        return legacy.format(v=version)
    return f"{model['hf'].split('/')[-1]}_uzblimp_{version}{ALPHABETS[alphabet]}"


def csv_path(model, alphabet, version=VERSION):
    """Per-pair results of a run: results/lm/<alphabet>/<model>.csv for the current version, the archived
    file for an earlier one."""
    if version == VERSION:
        return ROOT / "results" / "lm" / RELEASE_SCRIPT[alphabet] / f"{model['hf'].split('/')[-1].lower()}.csv"
    return ROOT / "archive" / "results" / f"{stem(model, alphabet, version)}.csv"


def load_runs(version=VERSION, keys=None, verbose=False):
    """{(key, alphabet): per-pair DataFrame indexed by pair id} for every run that is complete: its result
    file must hold exactly the pairs of the current benchmark (partial and outdated files are left out)."""
    with open(ROOT / "data" / "benchmark" / DATA["Latin"], encoding="utf-8") as f:
        ids = {line.split("\t", 1)[0] for line in f.read().splitlines()[1:]}
    runs = {}
    for m in MODELS:
        if keys and m["key"] not in keys:
            continue
        for alphabet in ALPHABETS:
            f = csv_path(m, alphabet, version)
            if not f.exists():
                continue
            df = pd.read_csv(f).set_index("id")
            if set(df.index) == ids:
                runs[(m["key"], alphabet)] = df
            elif verbose:
                print(f"not complete, left out: {f.name} ({len(set(df.index) & ids)}/{len(ids)} pairs)")
    return runs

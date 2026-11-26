# Gemini through the Gemini CLI (run on your own computer)

`scripts/gemini_cli_fc.py` sends the same 150-pair requests as the Claude and OpenRouter runs to Gemini through the
official Gemini CLI, signed in with your Google account (a Google AI Pro subscription raises the CLI's limits). Use
one account only: splitting the run across accounts to get around limits can break Google's terms and mixes quotas
and model versions.

## Steps

1. **Install Node.js 20 or newer** from nodejs.org, then the Gemini CLI:

   ```
   npm install -g @google/gemini-cli
   ```

2. **Sign in once:** run `gemini`, choose *Login with Google*, sign in with your Pro account in the browser. While it is
   open, type `/model` to see the model names you can use (write down the exact names, e.g. the current Pro and Flash
   models), and `/privacy` to see whether your prompts may be used to improve Google's models (opt out if offered).
   Leave with `/quit`.

3. **Get the repository and Python packages** (Python 3.11 or newer):

   ```
   git clone https://github.com/kattabeknorbaev/uzblimp
   cd uzblimp
   pip install pandas
   ```

   (If you already have it: `git pull`.)

4. **Check** that the CLI answers from a script:

   ```
   python scripts/gemini_cli_fc.py check
   ```

   It prints the CLI version, `answer: OK` and the model that answered. If it says JSON output is not supported, add
   `--plain` to the commands below.

5. **Trial: one request** (150 pairs, about a minute):

   ```
   python scripts/gemini_cli_fc.py trial --model MODEL_NAME
   ```

   It should print an accuracy for batch 1 and `tool calls` should not be reported. Send the output to Claude before
   going on if anything looks wrong.

6. **The run.** One order per pair, as the OpenRouter models (48 requests per model):

   ```
   python scripts/gemini_cli_fc.py run --model MODEL_NAME
   ```

   Or both orders, as the Claude models (96 requests): add `--passes AB`. The script waits 15 seconds between requests
   and saves every answer. When the daily limit is reached it stops with a message; run the **same command** later
   (e.g. the next day) and it continues where it stopped. A request whose answer was incomplete is tried once more; one
   where the model used a tool is not kept.

7. **Collect and push:**

   ```
   python scripts/gemini_cli_fc.py collect
   git add results/chat/gemini_cli scripts
   git commit -m "Gemini runs through the Gemini CLI"
   git push
   ```

   Then the results can be added to the paper (Appendix I, Table 21).

Repeat steps 5–7 for a second model (for example Flash after Pro) with its own `--model` name.

## What is recorded

- `runs/<model>_<alphabet>.json`: the answers per request, the model the CLI reports, the CLI's statistics.
- `<model>_<alphabet>.csv` (after `collect`): one row per answered pair and order.
- `responses/` (not in git): the CLI's raw output per request, kept on your computer so a run can resume.

## Differences from the other runs

The CLI adds its own system prompt and cannot be given temperature or an answer schema, so one line asking for the
answers as JSON is added to the end of each prompt. Gemini runs in an empty temporary folder with its file, shell,
memory and web tools switched off, so it cannot read the answer key in this repository or look the sentences up.

# Gemini through the Gemini CLI

`scripts/gemini_cli_fc.py` asks Gemini models the same 150-pair questions as the Claude, GPT and OpenRouter runs,
through the official Gemini CLI signed in with your Google account. The requests count against the daily limit of
your Google AI Pro subscription (1,500 model requests a day for the CLI), not against a paid API key. You run it on
your own computer, because the CLI signs in through your browser.

A full run of one model in both orders is 96 requests and takes a few hours. It can be stopped and continued at
any time, for example the next day when the daily limit has reset.

## 1. Install Node.js and the Gemini CLI

Install Node.js 20 or newer (the LTS version from nodejs.org, or on Windows `winget install OpenJS.NodeJS.LTS`).
Then open a new terminal and install the CLI version these runs were tested with:

```
npm install -g @google/gemini-cli@0.71.1
gemini --version
```

The second command should print `0.71.1`. This replaces any other version of the Gemini CLI on the computer;
afterwards you can update it again with `npm install -g @google/gemini-cli@latest`.

On Windows, if PowerShell says that running scripts is disabled on this system, use Command Prompt instead, or
type `npm.cmd` and `gemini.cmd` instead of `npm` and `gemini`.

## 2. Get the repository

```
git clone https://github.com/kattabeknorbaev/uzblimp
cd uzblimp
pip install pandas
```

If you already have it, run `git pull` in the `uzblimp` folder instead. All later commands run in that folder. On
Windows, if `python` is not found, use `py`.

## 3. Sign in once

```
python scripts/gemini_cli_fc.py login
```

Press Enter, and the Gemini CLI opens. Choose "Sign in with Google" with the arrow keys and Enter. The browser opens:
sign in with the Google account of your Google AI Pro subscription and allow access. Back in the terminal, when the
CLI shows its input box, type `/quit` and press Enter. The script then prints "Signed in".

The login is kept in its own folder, `.uzblimp-gemini` in your home folder, apart from any Gemini CLI you use
otherwise. Nothing of your own Gemini CLI setup (GEMINI.md, settings, extensions) reaches these runs.

## 4. Choose the models and check them

```
python scripts/gemini_cli_fc.py models
python scripts/gemini_cli_fc.py check --model gemini-3.1-pro-preview
```

`models` lists the models this CLI offers. Use the name in brackets, for example `gemini-3.1-pro-preview` (Pro) or
`gemini-3.8-flash` (Flash). Short names such as `pro` or `flash` are not accepted, because they can stand for
different models.

`check` sends one short question. It should show `sign-in method: Google account`, `answered by:
['gemini-3.1-pro-preview']` and end with `Ready.` If it says that the account cannot use the model, try another name
from the list.

## 5. One trial request

```
python scripts/gemini_cli_fc.py trial --model gemini-3.1-pro-preview
```

This asks one batch of 150 pairs in current Latin and prints one line with the accuracy on that batch, the time
the request took and the model that answered. It takes one to a few minutes.

## 6. The run

```
python scripts/gemini_cli_fc.py run --model gemini-3.1-pro-preview --passes AB
```

This sends 96 requests: 16 batches in each of the three alphabets, each pair once in each order, as in the Claude
and GPT runs. It prints one line per request and waits 15 seconds between requests. Keep the computer from going to
sleep while it runs (on Windows, in Settings, System, Power & battery).

When the daily limit is reached, the script stops with a message. Every answer so far is saved, so run the same
command later and it continues where it stopped. You can also stop it at any time with Ctrl+C. If you prefer to
start smaller, run it without `--passes AB` first (48 requests, one order); the same command with `--passes AB`
later adds only the other order.

Then do the same for a second model, for example `gemini-3.8-flash`.

## 7. Collect and push

```
python scripts/gemini_cli_fc.py collect
git add results/chat/gemini_cli
git commit -m "Gemini runs through the Gemini CLI"
git push
```

`collect` writes one file per model and alphabet and prints the accuracy of each. The raw CLI output in
`responses/` stays on your computer (it is not in git). The results can then go into the paper (Appendix I).

## If something goes wrong

| Message | What to do |
|---|---|
| The Gemini CLI was not found | Open a new terminal after installing, and check that `gemini --version` works. |
| The CLI is not signed in for these runs | Run `login` again and choose "Sign in with Google". |
| sign-in method is not "Google account" | Run `login` again and choose "Sign in with Google", not an API key. |
| The CLI cannot use the model | Pick another name from `models`. |
| ... was answered by X, not by Y | Give the full model name from `models`. |
| The daily limit or a rate limit was reached | Wait (until the next day for the daily limit) and run the same command. |
| no complete list of 150 answers | Nothing to do: the request is asked once more automatically. |

If anything else looks wrong, send the output of `check` and of the last command.

## How the runs are kept comparable

- Every request is one of the 96 requests of the Claude runs (`scripts/claude_fc.py`), unchanged, with one line
  added at the end that asks for the answers as JSON, because the CLI cannot be given an answer schema.
- The CLI runs with its own profile folder (`GEMINI_CLI_HOME`), in an empty temporary folder, under a policy that
  denies every tool. Gemini is offered no tools, so it cannot read the answer key in this repository, run commands
  or search the web. An answer in which it still tried a tool is not kept.
- The model is pinned with `-m`. The CLI's statistics name the model that answered each request; if it is not the
  model asked for, the run stops and nothing of that request is kept. In this mode the CLI does not switch models
  when a limit is reached; it stops with an error.
- The CLI adds its own system prompt and chooses the sampling settings; version 0.71.1 sends Gemini 3 models
  temperature 1 and thinking level high. These cannot be changed from the command line, so they are recorded as the
  CLI's defaults.

## What is recorded

- `runs/<model>_<alphabet>.json`: the answers per request, the model that answered, the CLI's statistics and the
  CLI version.
- `<model>_<alphabet>.csv` (after `collect`): one row per pair and order, in benchmark order.
- `responses/` (not in git): the CLI's output per request, so that a run can continue where it stopped.

## A second Google account

Use one account for the whole run of a model, and do not switch accounts to get around the daily limit; wait for
it to reset instead. To run another model with a second account, give that account its own profile folder before
`login` and before every later command, for example in PowerShell `$env:UZBLIMP_GEMINI_HOME="$HOME\.uzblimp-gemini-2"`
or in Command Prompt `set UZBLIMP_GEMINI_HOME=%USERPROFILE%\.uzblimp-gemini-2`.

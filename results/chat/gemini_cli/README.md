# Gemini through the Gemini CLI

`scripts/gemini_cli_fc.py` asks Gemini models the same 150-pair questions as the Claude, GPT and OpenRouter runs,
through the official Gemini CLI signed in with your Google account. The requests count against the daily limit of
your Google AI Pro subscription (up to 1,500 model requests a day for the CLI; the newest preview models may have a
lower limit), not against a paid API key. You run it on your own computer, because the CLI signs in through your
browser.

A full run of one model in both orders is 96 requests and takes a few hours. It can be stopped and continued at
any time, for example the next day when the daily limit has reset.

## 1. Install Node.js

Install Node.js 20 or newer: the LTS version from nodejs.org, or on Windows `winget install OpenJS.NodeJS.LTS`.
Then open a new terminal and check that `node --version` prints v20 or higher.

## 2. Get the repository

```
git clone https://github.com/kattabeknorbaev/uzblimp
cd uzblimp
pip install pandas
```

If you already have it, run `git pull` in the `uzblimp` folder instead. All later commands run in that folder. On
Windows, if `python` or `pip` is not found, use `py` and `py -m pip`.

## 3. Install the Gemini CLI for these runs

```
python scripts/gemini_cli_fc.py setup
```

This installs Gemini CLI 0.71.1, the version these runs were tested with, into its own folder,
`.uzblimp-gemini/cli` in your home folder, and ends with "Gemini CLI 0.71.1 is installed for these runs". A Gemini
CLI you use otherwise is not changed, and updates of it do not change these runs.

## 4. Sign in once

```
python scripts/gemini_cli_fc.py login
```

Press Enter, and the Gemini CLI opens in the terminal:

1. "How would you like to authenticate for this project?": "Sign in with Google" is selected; press Enter.
2. "Opening authentication page in your browser. Do you want to continue?": "Yes" is selected; press Enter.
3. In the browser, sign in with the Google account of your Google AI Pro subscription and allow access.
4. Back in the terminal, the CLI says "You've successfully signed in with Google. Gemini CLI needs to be
   restarted. Press R to restart": press R.
5. When the input box ("Type your message") appears, type `/quit` and press Enter.

The script then prints "Signed in with your Google account". The login is kept in its own profile folder,
`.uzblimp-gemini` in your home folder (a file there that only you can read), apart from any Gemini CLI you use
otherwise. Nothing of your own Gemini CLI setup (GEMINI.md, settings, .env files, extensions) reaches these runs.
Running `login` again always asks you to sign in again.

## 5. Choose the models and check them

```
python scripts/gemini_cli_fc.py models
python scripts/gemini_cli_fc.py check --model gemini-3.1-pro-preview
```

`models` lists the models the CLI offers your account, each with its name in brackets. Give `--model` that name.
The commands here use `gemini-3.1-pro-preview`; if your list does not have it, use the newest Pro model in the
list, here and in the steps below. Short names such as `pro` or `flash` are not accepted, because they can stand
for different models.

`check` sends one short question. It should print `sign-in: Google account`, then `answered by:
['gemini-3.1-pro-preview']`, and end with `Ready.` If it says that the account cannot use the model, try another
name from the list.

## 6. One trial request

```
python scripts/gemini_cli_fc.py trial --model gemini-3.1-pro-preview
```

This asks one batch of 150 pairs in current Latin and prints one line with the accuracy on that batch, the time
the request took and the model that answered. It takes one to a few minutes.

## 7. The run

```
python scripts/gemini_cli_fc.py run --model gemini-3.1-pro-preview --passes AB
```

This sends 96 requests: 16 batches in each of the three alphabets, each pair once in each order, as in the Claude
and GPT runs. It prints one line per request and waits 15 seconds between requests. Keep the computer from going to
sleep while it runs: on Windows in Settings, System, Power & battery; on macOS by starting the command with
`caffeinate -i`, as in `caffeinate -i python scripts/gemini_cli_fc.py run ...`.

When the daily limit is reached, the script stops with a message. Every answer so far is saved, so run the same
command later and it continues where it stopped. You can also stop it at any time with Ctrl+C. If you prefer to
start smaller, run it without `--passes AB` first (48 requests, one order); the same command with `--passes AB`
later adds only the other order.

Then do the same for a second model, for example the newest Flash model in the list.

## 8. Collect and push

```
python scripts/gemini_cli_fc.py collect
git add results/chat/gemini_cli
git commit -m "Gemini runs through the Gemini CLI"
git push
```

`collect` writes one file per model and alphabet, prints the accuracy of each and how many of the 2,400 pairs
have an answer in each order, and names any batch still without one (the `run` command asks those again). The raw
CLI output in `responses/` stays on your computer (it is not in git). The results can then go into the paper
(Appendix I).

## If something goes wrong

| Message | What to do |
|---|---|
| Node.js was not found, or is too old | Install Node.js 20 or newer and open a new terminal. |
| The Gemini CLI for these runs is not installed | Run `setup`. |
| The CLI is not signed in for these runs | Run `login`. |
| ... signs in with ..., not with your Google account | Run `login` and choose "Sign in with Google". |
| The CLI could not use the saved login | Check the internet connection and run the same command again; if it repeats, run `login`. |
| The daily limit ... was reached | Run the same command again after the time the CLI names (usually the next day). |
| Google's servers had no capacity | Run the same command again in a few minutes. |
| A usage limit was reached | Wait a while and run the same command again. |
| Google asks you to verify your account | Open the link it shows, signed in with the same account, then run the same command again. |
| The CLI cannot use the model | Pick another name from `models`. |
| ... was answered by X, not by Y | Give the full model name from `models`. |
| no complete list of 150 answers, or tried a tool call | Nothing to do: the batch is asked once more right away. |
| Without a usable answer so far: ... | Run the same command again: those batches are asked again. |

If anything else looks wrong, send the output of `check` and of the last command.

## How the runs are kept comparable

- Every request is one of the 96 requests of the Claude runs (`scripts/claude_fc.py`), unchanged, with one line
  added at the end that asks for the answers as JSON, because the CLI cannot be given an answer schema. The prompt
  goes to the CLI as UTF-8 bytes, so it is the same on every system, and `collect` checks each saved answer against
  the prompt's SHA-256.
- The CLI is its own copy of version 0.71.1 (`setup`). It does not update itself, the run stops if it reports
  another version, and each request records the version.
- The CLI runs with its own profile folder (`GEMINI_CLI_HOME`), in an empty temporary folder with an empty `.env`
  file above it, under a policy that denies every tool. Gemini is offered no tools, so it cannot read the answer key
  in this repository, run commands or search the web. An answer in which it still tried a tool is not kept.
  Environment variables of an everyday Gemini CLI setup that would change the requests (a default model, a
  replaced system prompt, a Google Cloud project) are not passed on. Usage statistics are off in this profile.
- The model is pinned with `-m`. The CLI's statistics name the model that answered each request; if it is not the
  model asked for (or a dated version of it), the run stops and nothing of that request is kept. In this mode the
  CLI does not switch models when a limit is reached; it stops with an error.
- The CLI adds its own system prompt and chooses the sampling settings; version 0.71.1 sends Gemini 3 models
  temperature 1, top-p 0.95, top-k 64 and thinking level high. These cannot be changed from the command line, so
  they are recorded as the CLI's defaults.

## What is recorded

- `runs/<model>_<alphabet>.json`: per request the answers, which try gave them, the model that answered, the CLI's
  statistics, the CLI version, the time, and the prompt's length and SHA-256.
- `<model>_<alphabet>.csv` (after `collect`): one row per pair and order, in benchmark order.
- `responses/` (not in git): the CLI's output per request, so that a run can continue where it stopped.

## A second Google account

Use one account for the whole run of a model, and do not switch accounts to get around the daily limit; wait for
it to reset instead. To run another model with a second account, give that account its own profile folder before
`login` and before every later command, for example in PowerShell `$env:UZBLIMP_GEMINI_HOME="$HOME\.uzblimp-gemini-2"`,
in Command Prompt `set UZBLIMP_GEMINI_HOME=%USERPROFILE%\.uzblimp-gemini-2`, or on macOS
`export UZBLIMP_GEMINI_HOME=~/.uzblimp-gemini-2`. Both accounts use the same copy of the CLI, so `setup` is not
needed again.

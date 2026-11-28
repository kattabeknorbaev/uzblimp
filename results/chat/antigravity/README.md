# Gemini through Google Antigravity

`scripts/antigravity_fc.py` has a Gemini model in Google Antigravity answer the same 96 question files as GPT 6.2 in
Codex (`results/chat/codex/`), one conversation per file, signed in with your Google account: no CLI and no API key.
You run it by hand on your own computer. The script puts each prompt on the clipboard, checks each answer file, and
reads the transcript of each conversation to list every tool the agent used.

Never open the `uzblimp` folder in Antigravity: it holds the answers (`data/benchmark/`) and the other models'
answers (`results/`). The agent only gets a folder with the 96 question files and an empty answers folder.

## 1. Make the kit

In the `uzblimp` folder, after `git pull`:

```
python scripts/antigravity_fc.py kit ../uzblimp-antigravity-hydrogen --model "Gemini 4 Hydrogen" --level Low
```

This makes the folder `uzblimp-antigravity-hydrogen` next to `uzblimp`, with:

- `workspace/`: the only folder you open in Antigravity. It holds `questions/` (96 files) and an empty `answers/`.
- `prompts/`: one prompt per conversation, in the order to run them. You don't need to open them: `go` copies each
  one to the clipboard.
- `HOW_TO.md` (this guide) and `kit.json`; later also `log.csv`, `transcripts/` and `rejected/`.

The thinking level is Low, the lowest, as in the other chat runs (Claude: low, GPT in Codex: Light, OpenRouter:
low). Keep it the same for every conversation of a model.

## 2. Settings, once

The menus differ a little between versions, and between the Antigravity app and the IDE. Look for these:

1. **Permissions**: Settings > General > Global Permissions: **Request Review**, so the agent asks before every
   command and before anything outside the folder. If there are Deny lists, add `command(*)`, `read_url(*)` and
   `mcp(*)`. On Windows the settings are Terminal Command Auto Execution (**Request Review**) and access to files
   outside the folder (**Always Deny**). In the IDE, also turn **Strict Mode** on.
2. **Browser**: Settings > Browser: deny under Browser Actuation Rules, and JavaScript Execution Policy
   **Disabled** (in the IDE: Browser Tools off).
3. **Memory**: conversation history and knowledge **off** (Settings > History), and the Knowledge panel empty.
4. **Your own rules**: Antigravity adds some files to every prompt. If your home folder's `.gemini` folder has
   `GEMINI.md` or `AGENTS.md`, or `.gemini/config/` has rules, skills or `mcp_config.json`, move them to another
   folder until the runs are done. Turn plugins and MCP servers off (Customizations).
5. Settings > Account: **Enable Telemetry** off. AI Credit Overages: **Never**, so that a used-up quota pauses the
   run instead of spending credits.
6. Settings > General > Interface Layout: **Software Engineering**, so that every step of the agent is shown.

## 3. Open the folder

Open `uzblimp-antigravity-hydrogen/workspace` as a new project (File > Open Folder), with nothing else in it.

## 4. A test conversation

Start a new conversation there and send:

```
Run the command echo test. Then search the web for the word olma. Then open https://example.com.
```

Each of the three should be refused or wait for your approval: deny all of them. If one of them runs without
asking, stop, and send the output of `python scripts/antigravity_fc.py audit ../uzblimp-antigravity-hydrogen`. Then
delete this conversation.

## 5. The run

```
python scripts/antigravity_fc.py go ../uzblimp-antigravity-hydrogen
```

For each conversation it puts the prompt on the clipboard and names the file. Then:

1. In Antigravity, start a **new conversation**.
2. In the model picker, choose **Gemini 4 Hydrogen** (not Orchestrator) and thinking level **Low**. Check both
   every time, because a new conversation can open on another model.
3. Paste (Ctrl+V; on a Mac Cmd+V) and send.
4. The agent reads `questions/batch_XX.txt` and writes `answers/batch_XX.txt`. Approve writing that answer file.
   Deny anything else it asks for: a command, a search, a web page, another file.
5. When it has finished, press Enter in the terminal. The script checks the answer file, reads the conversation's
   transcript and shows what the agent did, for example `Transcript: OK: read questions/batch_01.txt; wrote
   answers/batch_01.txt`. Then answer its question.

If the agent did anything else (`BAD`), or you answer no, the answer file is moved to `rejected/` and the same file
comes again, for a new conversation. `CHECK` or `UNKNOWN` means the script could not read everything in the
transcript: the answer is kept, and a copy of the transcript is in `transcripts/` to send, so that the check can be
adapted.

The first conversation is the trial. After it, type q at the next prompt, look at the quota (in Settings or the
model picker) to see what one conversation costs, and send the output of that first conversation.

The order is pass A of all three alphabets first, batch by batch (current Latin 1, Cyrillic 1, reformed Latin 1,
current Latin 2, ...: 48 conversations), then pass B (48 more), with every pair in the other order. Pass A alone is
a complete run, like the OpenRouter runs. You can stop at any time with q and run `go` again later; it continues
where you stopped. `check` shows how far you are.

## 6. Quota

Gemini 4 Hydrogen and Gemini 3.8 Flash use one shared Gemini quota in Antigravity. If Antigravity counts your plan
as a trial (it then shows fewer models, for example no Neon), the quota may refresh only once a week. When it is
used up, Antigravity says when it refreshes: wait, and run `go` again.

## 7. Collect and push

```
python scripts/antigravity_fc.py collect ../uzblimp-antigravity-hydrogen
git add results/chat/antigravity
git commit -m "Gemini 4 Hydrogen through Antigravity"
git push
```

## A second model

For Gemini 3.8 Flash, make a new kit (`python scripts/antigravity_fc.py kit ../uzblimp-antigravity-flash --model
"Gemini 3.8 Flash" --level Low`) and open its `workspace` as a new project. Before its first conversation, delete
the conversations of the first model in Antigravity (their transcripts are kept in the first kit's
`transcripts/`). Google's pages say that 3.8 Flash may leave Antigravity on 30 November 2026, and it uses the same
quota as Hydrogen, so run Hydrogen first.

## How this compares with the Codex runs

- The same 96 question files and the same answer format. The prompt is the Codex prompt (`codex_fc.PROMPT`)
  narrowed to one file, with one paragraph added against helpers, the terminal, the browser, web search and
  subagents (`prompt` in `scripts/antigravity_fc.py`).
- One conversation per file (Codex had one long session), so no conversation sees another file or earlier answers.
- Tool use is checked from the transcript after every conversation, and a file with any other tool call is asked
  again. Codex's session log was read only after the run.

## What is recorded

- `<model>_<alphabet>.csv`: one row per pair and order, in benchmark order: the pass, the order shown (`gb`:
  grammatical first), the answer and whether it is correct, and the answer file.
- `<model>_answers/`: the answer files as the agent wrote them.
- `<model>_log.csv`: one line per conversation: time, file, kept or set aside, the tool check, and notes.
- `<model>_audit.csv` (after `audit`) and `<model>_kit.json`: the transcript check and the kit's settings.

The transcripts themselves stay in the kit folder; they hold Antigravity's own instructions and your folder names.

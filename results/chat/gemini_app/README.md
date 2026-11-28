# Gemini in the Gemini app

`scripts/gemini_app_fc.py` has a Gemini model in the Gemini app (gemini.google.com) answer the requests of the Gemini
CLI route, one temporary chat per request, by hand: no CLI and no API key. Each request is the request of the Claude
runs with one line asking for the answers as JSON. The script puts each request on the clipboard, reads Gemini's
answer from the clipboard once you have copied it, checks it, and saves it once you confirm.

Run the commands below in a terminal in the `uzblimp` folder. On Windows, use `py` if `python` is not found.

## 1. Make the kit

In the `uzblimp` folder, after `git pull`:

```
python scripts/gemini_app_fc.py kit ../uzblimp-gemini-app-neon --model "Gemini 4 Neon" --picker "Deeper analysis" --level Low
```

This makes the folder `uzblimp-gemini-app-neon` next to `uzblimp`, with `paste/` (the 96 requests), `answers/`
(empty) and `HOW_TO.md` (this guide, with the kit's own commands at the top). `--picker` is the name the model
picker shows for the model.

The thinking level is Low, the lowest, as in the other chat runs (Claude: low, GPT in Codex: Light, OpenRouter:
low). Keep it the same for every chat.

## 2. Settings, once

On gemini.google.com in a desktop browser, signed in with your personal Google account (menus change from time to
time; look for these):

1. Settings & help > Personal Intelligence: **Memory** off, your **Instructions for Gemini** removed or paused, and
   **Connected Apps** off. You can turn them back on after the runs.
2. Settings > Usage limits (or gemini.google.com/usage): look at how much is left. Leave the switch that spends AI
   credits off.

## 3. The run

```
python scripts/gemini_app_fc.py go ../uzblimp-gemini-app-neon
```

For each request it puts the request on the clipboard and names it. Then:

1. On the Gemini home page, click **Temporary chat** (top right).
2. In the model picker, choose **Deeper analysis** (Gemini 4 Neon) and thinking level **Low**. Set both every
   time.
3. Check that **Chat** (not Task) is selected and that the prompt box shows no "Search Google" chip. Don't use the
   + menu (Search Google, Canvas, Deep Research).
4. Click into the prompt box, paste (Ctrl+V; on a Mac Cmd+V) and send.
5. Wait until the answer is complete. Don't press "Answer now", and don't regenerate.
6. Click the copy button below the answer, then press Enter in the terminal. The script checks that the clipboard
   holds 150 answers.
7. It then asks whether everything was right: type `y` if there is no Sources button below the answer, no "Limit
   reached", and the picker still shows Deeper analysis and Low; otherwise type `n`. A note may follow, for example
   `n Sources shown`. Only after `y` is the answer saved; after `n` the same request comes again, for a new
   temporary chat.

The first chat is the trial, with the longest request (current Latin, batch 4); the same batch in Cyrillic and
reformed Latin comes next. After sending the trial, scroll to the end of your message: it must end with the line
"Reply with JSON only, ...". If it doesn't, the message box cut the request: type `q` and send what you see. Look
at the usage before and after the trial, to see how much one chat uses.

If a temporary chat does not let you choose the model and the thinking level, use a normal new chat and switch
Personal Intelligence off for that chat (under Tools in the prompt box), and add that as a note: `y normal chat`.

When "Limit reached" appears, that answer may already come from another model (Flash-Lite): type `n limit
reached`, then `q` at the next step, and come back when the limit has refreshed (every 5 hours, up to a weekly
limit).

The order after the trial is pass A of all three alphabets, batch by batch (current Latin 1, Cyrillic 1, reformed
Latin 1, current Latin 2, ...: 48 chats), then pass B (48 more), with every pair in the other order. Pass A alone is
a complete run, like the OpenRouter runs. You can stop at any time with `q` and run `go` again later; it continues
where you stopped. `check` shows how far you are. Each chat takes a few minutes, so pass A takes some hours, spread
over several sessions.

If the script says it has no access to the clipboard, copy by hand: open the paste file it names, copy all of it and
paste it into Gemini; save Gemini's answer as `reply.txt` in the kit folder (UTF-8); then press Enter.

## 4. Collect and push

```
python scripts/gemini_app_fc.py collect ../uzblimp-gemini-app-neon
git add results/chat/gemini_app
git commit -m "Gemini 4 Neon in the Gemini app"
git pull --rebase
git push
```

## How this compares with the other runs

- Each request is exactly the request of the Gemini CLI route (`gemini_cli_fc.prompt_for`): the request of the
  Claude runs, unchanged, with one line asking for the answers as JSON.
- One temporary chat per request, so the requests are independent, as in the Claude and OpenRouter runs.
- The app adds its own instructions, and only the model and the thinking level can be chosen. It also decides by
  itself whether to use Google Search; answers that showed Sources are set aside and asked again, but search cannot
  be switched off, so the record says only that no kept answer showed Sources.

## What is recorded

- `<model>_<alphabet>.csv`: one row per pair and order, in benchmark order: the pass, the order shown (`gb`:
  grammatical first), the answer and whether it is correct, and the answer file.
- `<model>_answers/`: Gemini's answers as copied.
- `<model>_log.csv`: one line per chat: time (UTC), request, model and level, kept or set aside, and notes.
  `<model>_kit.json`: the kit's settings.

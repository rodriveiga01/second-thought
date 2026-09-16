# ⏱️ TimeCop — BEGINNERS: START HERE (~6 minutes)

**One sentence:** TimeCop looks at a terminal command *before* it runs and stops you if it looks like it will delete everything, leak a password, or break your team's shared work. Spell-check, but for disasters.

**Start in 10 seconds, no typing:** double-click **`Start Here.command`** in this folder. A terminal opens and runs the check-up, then waits on "Press Enter to close" so you can read — Enter closes the window.
If your Mac warns you: that's what macOS does with *every* program from the internet, virus or not — it's saying "I don't know this author," not "this is a virus." Right-click it → Open tells your Mac "I trust this one file." Everything it runs is readable text in this folder; there is nothing hidden.

**Or with one line:** drag **`timecop-cli`** into any terminal window, type a space and a task word like `test`, press Enter.

Safety up front: the check-up, the drill, and judging commands **never run anything** — they read words and print opinions, like reading a recipe instead of cooking. Run them 100 times: zero files harmed. Right now protection is **off** (it's just files). Everything here is **$0** until you add an AI key (Step 6, optional) — no account, no card on file, so **you cannot be charged**.

Task words (every command starts with `./timecop-cli` + one of these): `test` check-up · `demo` safety drill · `check` judge one command · `setup` turn protection on · `remove` turn it off · `diary` read the log in plain words · `clean` tidy the log. (Older twins still work: doctor=test, reel=demo, init=setup, uninstall=remove. Two names, same jobs — kept so old instructions don't break.)

---

## 1. What's in this folder?

| Name | What it is |
|---|---|
| `Start Here.command` | Double-click starter (runs the check-up). |
| `timecop-cli` | The remote control. Don't double-click it (it opens as text — that's normal, you didn't break it: it has no `.app`/`.exe` ending because it's a helper *for* the terminal, not a desktop app). Drag it into a terminal instead. Opened any file by accident? Nothing happens — reading files never runs them. |
| `README.md` | The short programmer manual. This file is the long beginner one. |
| `timecop/` | The engine (5 small program files). Code-looking is normal; you never need to open these. |
| `hooks/` | One glue file connecting the engine to your terminal. Weird symbols like `zle -M` are the shell's language, not homework. |
| `reel/` | The safety drill (11 labeled scenarios as text) + the diary file. |
| `docs/` | This guide + design notes. |
| `.next/` | Leftover from a *different* project that once lived in this folder. Not TimeCop, not a virus. Safe to delete (that project rebuilds it if needed) — or just ignore it. |
| `.DS_Store` | Junk macOS drops in every folder. Does nothing. Safe to delete (macOS remakes it) — or ignore it. |
| `__pycache__/` | Appears by itself after you run things — Python's own speed notes. Normal, not a virus. |

## 2. Getting a terminal to this folder

"Terminal" = the black-box app (macOS calls it Terminal). "Inside this folder" = the window is *looking at* this folder, so short commands work.

- Easiest: in Finder, right-click the folder → **Services → New Terminal at Folder**. (If you don't see it: Finder → Settings → Services → tick it. One-time.)
- Or drag the folder into a terminal window and press Enter.
- `./` means "right here": `./timecop-cli` only works when the window is already inside this folder. From anywhere else (`/tmp`, home…) you get `no such file or directory ... EXIT:127` — that's the terminal saying "not here," not something broken. Fix: drag `timecop-cli` into the window instead (that pastes the full location, which works from anywhere), then add your task word.
- Spaces: the terminal splits words on spaces, so `test 1` looks like two things. Quotes glue it back together: `cd "/Users/.../test 1"`. That's the whole story — no hate, just glue.

## 3. Check-up: `./timecop-cli test`

Typical output (your millisecond numbers will differ run to run — normal, not an error):

```text
TimeCop self-test — SAFE: this only reads words and prints opinions. Nothing runs. Cost $0.
[PASS] Everyday command recognized ("ls" waves through)
[PASS] Mass-delete stopped ("sudo rm -rf /" would be blocked — it was NOT run)
[PASS] Shared-work overwrite stopped ("git push --force main" would be blocked — it was NOT run)
[NOTE] No AI key — the free built-in rules are active ($0).
       NOTE means 'one optional thing missing', not 'you failed'.
       Add a key for real AI protection (README step 6).
Done in about 20ms (ms = milliseconds, thousandths of a second).
Verdict: TimeCop works. The only thing that changed: a few diary lines. Nothing else was touched.
```

Line by line:
- `ls` is "boring" = one of 11 everyday commands on a fixed safe list (`ls`, `cd`, `pwd`, `echo`, `cat`, `git status`, `git diff --stat`, `git log`, `whoami`, `date` — plus bare `cd`). That's the whole list, right here. Waved through instantly, free, because none of them can destroy anything. One exception: if the command contains shell operators (`; | & $ \` > <` or multiple lines), it always gets the full check even when it *starts* with a boring word — `ls; rm -rf /` starts with `ls` and still gets judged.
- "nuke-prod" is our nickname for the mass-delete test. Nicknamed, never executed.
- `[PASS]` = works. `[NOTE]` = works, one *optional* thing missing (the key). Not failure.
- No key → **built-in rules**: fixed examples stored on your laptop. Free forever, no internet. The real AI ("Jev" — not a person, just the AI model, version `jev-latest`) only enters with a key (Step 6).
- Yes, the diary grew a few lines — that IS the "one thing that changed" (Step 5).
- `EXIT:0` after a command = the traffic light below, all green here.

## 4. Judge one command: `./timecop-cli check "..."`

**Why the quotes?** Quotes put a multi-word command in one envelope. Without them, `check rm -rf /` scatters into pieces and you get `unrecognized arguments: -rf /` *plus* a hint line explaining the quotes. With quotes, `check "rm -rf /"` arrives whole. (Same glue idea as the folder-with-spaces above.)

- `check "ls"` → `OK — looks safe. ($0.00, instant.)` Short, because there's nothing scary to explain. (Warn/block answers still spell out "never runs anything.")
- `check "sudo rm -rf /"` → `STOP — this deletes files permanently...` "Protected terminal" = a terminal with protection turned ON (Step 7) — yours isn't, so YES does nothing here, and `check "YES"` now *says that* instead of a confusing OK.
- `check "rm -rf ./build"` → warning. Warnings still run in a protected terminal — their job is "slow down and look," not "stop." Stops are for the irreversible stuff.
- **Traffic light** (`echo EXIT:$?` shows the last one): 0 green fine · 1 yellow warning, carried on · 2 red stopped on purpose. Red is 2 (not 1) because the connector needs three distinct signals. None mean "crashed."
- `--live` without a key now says so out loud ("used the free built-in rules instead. Nothing was spent.") — `live` = real AI over the internet, `dry-run` = built-in rules, `local` = instant safe-list. The diary logs which one judged. If live was asked for but the network/key failed mid-call, the diary adds "live unavailable" instead of pretending — a fallback that admits it's a fallback.
- `--cwd --repo --branch --ssh-host` = context (which folder = cwd, which project = repo; which code branch; which remote computer = ssh-host, usually your own). Skip them forever — a protected terminal fills them in.
- Wrong words: no task word → runs the self-test (bare means "just check me"). `hello` → "I don't know the job 'hello'. Did you mean…? I know: test, demo, check, setup, remove, diary, clean" (older twins accepted quietly: doctor, reel, init, uninstall). Strict on purpose — guessing near delete-commands would be reckless.

## 5. Drill + diary: `./timecop-cli demo`

11 rounds = 5 disasters + 3 everyday cases + 3 command-smuggling cases (why not 10: that's just how many scenarios we wrote).

Mugshots translated: pasted web installer · mass delete · password upload · shared-work overwrite · lying "cleanup" tip. `curl … | sudo bash` = "download something and run it as administrator" (`curl` fetches, `bash` runs). `evil.example` is a *reserved* fake address — officially set aside so it can never be a real site — and anyway nothing runs: textbook, not wildlife. `disasters.json` lists them one labeled block each, with the expected verdict attached.

`6 stopped, 3 warnings shown, 2 allowed` with all-`[PASS]` lines: PASS grades *the tool* ("it reacted as designed"), stopped/allowed is what happened to each *command*. Both true at once.

**Diary** (`reel/receipt.jsonl` — `.json` = structured text, `.jsonl` = one record per line): skip reading it raw; use `./timecop-cli diary`:

```text
Diary — last 3 checks (plain words; full details stay in reel/receipt.jsonl):
  2026-09-16 12:30 — STOPPED 'sudo rm -rf /', 96% sure (built-in rules)
  2026-09-16 12:31 — allowed 'ls -la' (built-in rules)
```

Raw-field decoder (if curious): `danger_p: 0.97` = 97% sure it's dangerous (decimals are percents — 0.97 means 97%; `diary` translates for you). `confidence: 0.92` = 92% sure *of its own judgment*. `risk: 2.0` = top of the 0–2 ruin scale (0 harmless → 2 permanent destruction). `[REDACTED-AWS-KEY]` = proof hiding worked — the secret was swapped for a marker *before* saving/sending. Want to see one with zero risk? Run `./timecop-cli check "git push # key AKIAIOSFODNN7EXAMPLE"` — that key is a famous *fake* example (ends in EXAMPLE, works nowhere), and your diary will show the marker instead. Grows by appending (normal); `clean` files old pages into `receipt-archive.jsonl` (the attic — safe to delete whenever you like); deleting the diary file works too.

## 6. The key (optional — skip freely)

Without it: built-in rules, $0, forever — but understand what those are: 11 choreographed scenarios known by heart. Anything outside that list waves straight through. That's rehearsal and demo material, not protection. With a key: Jev judges your *actual* tricky commands.

**Money, plainly:** the AI bills per million text-chunks (a "chunk" ≈ 4 letters; "MTok" = million chunks). You pay $0.042/million for what you *send*; the answers come back free. One scary check ≈ a few hundred chunks ≈ **$0.00002**. Boring commands never call the AI ($0). A whole demo evening ≈ $0.003. "My $5 project budget" = *my* testing allowance while building this, not your bill — and since there's no account, no card, and no payment anywhere in this tool, charging you is *impossible*. (The *optional key* below needs their free account — the one exception to "no account." Even it has no payment.)

**Adding it:** `console.typesafe.ai` → sign in (yes, this step needs an account — everything else doesn't) → Settings → Keys → create → copy. Then type exactly `security add-generic-password -s timecop-jev -a "$USER" -w` — `$USER` literally (computer fills in your name); `security` = macOS's password-manager tool. Press Enter: the blank line **is** the input box (password boxes show no dots — that's normal, not a frozen keyboard). Paste (Cmd+V), Enter, done. Verify it worked: run `./timecop-cli test` — the key line flips to `[PASS] AI key: found.` "History" = the terminal remembers typed lines (press ↑); pasting into that prompt skips the memory — the whole reason for the dance.

## 7. Protection ON/OFF (only when ready)

Your terminal reads a settings file on every launch: `~/.zshrc` (`~` = your home folder). A "shell hook" = one line in that file loading TimeCop into new terminals. `source "…"` = "load this file now". `export TIMECOP_OFF=1` = stick a note named TIMECOP_OFF saying 1 (= paused); `unset TIMECOP_OFF` peels it off.

```sh
./timecop-cli setup --write
```

(`setup` alone only *prints* the 4 steps — showing before doing, so `--write` never surprises you. It adds one line, after copying settings to `~/.zshrc.bak` — the backup *is* supposed to sit in your home folder; that's the undo button, not trash.)

**What "on" looks like:** nearly nothing — until you test it. First, the zero-fear test: `./timecop-cli demo` (text only, nothing can run). Then the real proof, and here's why it's safe: in a protected terminal your Enter key does NOT run the command — TimeCop sees it *first* and either allows or stops it. So type `ls` → runs. Type `sudo rm -rf /` → red STOP, *nothing happens*. The scary command is the *safest* test, because the check happens before execution, every time. That's on. (Keyless: one reminder line per new terminal until you add a key — one line, not spam.)

Two rules for protected life, especially juniors: a **warning** means stop and read, not "press Enter again" — and **YES is not muscle memory**. YES re-runs a blocked command sight-unseen; if you type it without reading, you've built a one-word self-destruct. TimeCop is a seatbelt, not a replacement for backups, least-privilege accounts, or prod access controls.

**Fail-open, concretely:** every error path ends in "let the command run." Delete this whole folder and terminals still open fine (TimeCop just silently skips). It cannot lock you out — there's no code path that blocks without the AI voting first, and no-AI means allow.

**Pause** (this window): `export TIMECOP_OFF=1`. Un-pause: `unset TIMECOP_OFF` or new window. **Uninstall:** `./timecop-cli remove` (backup kept). "Never turned on, nothing to undo" = precisely true: no line was ever added.

## 8. Leftover words, one line each

- **"Jev only votes"** = multiple-choice answers, never sentences — so it can't invent a fake command at you.
- **Builder words you can ignore** (`noul`, `choice`, `score`, `TOCTOU`, `bracketed-paste`, …): internals from `docs/` that you'll never type or see in outputs. Skipping them loses nothing.
- **allowlist / blocklist** = instant free lists (wave-through / hide-secrets-first). Not social-media blocking.
- **confidence gate** = stops only when ≥85% sure (0.85); 55% gets a warning. Diary 0.92s are those percents.

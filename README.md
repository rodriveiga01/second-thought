# Second Thought ⏱️

[![test](https://github.com/rodriveiga01/second-thought/actions/workflows/test.yml/badge.svg)](https://github.com/rodriveiga01/second-thought/actions/workflows/test.yml)

The most expensive keystroke on your keyboard is **Enter**.

Every engineer collects a story about it. `rm -rf` one folder too high. A database
command meant for localhost landing on prod. `git push --force main` wiping a
teammate's afternoon. A `curl | bash` installer nobody vetted. An AWS key pushed
before anyone noticed. One command, a few seconds, permanent. Reviews, CI, and
backups all help *around* that moment — nothing watches the moment itself.

Second Thought sits in that moment. It's a terminal seatbelt: every shell command
gets judged **before** it runs — **allow, warn, or block** — and then life goes on.
Green means go. Yellow means stop and read. Red means it didn't run. It's not a
self-driving car and it doesn't pretend to be one: a seatbelt, not a replacement
for backups, least-privilege, or access controls.

Under the hood, a calibrated AI judge (Jev, a TypeSafe System One model) answers
multiple-choice questions about your command — *dangerous? which kind? how sure?* —
instead of generating text, so it can't hallucinate commands back at you. Boring
commands like `ls` never leave your laptop. Scary ones cost about a millionth of
a dollar to judge. Anything the judge can't reach — offline, slow, no key — fails
open to allow, and admits it in the log.

New to terminals? Start with [`docs/BEGINNERS.md`](docs/BEGINNERS.md) instead —
this page assumes you know your way around a shell.

## Taste it in 60 seconds

```sh
git clone https://github.com/rodriveiga01/second-thought.git && cd second-thought
pip install -e .              # or skip install: ./second-thought works too
second-thought demo           # the 12-scenario drill — $0, nothing runs
```

You'll see the tool stop five disasters, flag three maybes, and wave through two
everyday commands — all as text on screen, none of it executed. That drill is the
whole product in miniature. If you like what you see:

```sh
second-thought test           # self-test: gates, key status, latency
second-thought setup --write  # protection on: one line into ~/.zshrc (backup first)
```

Then open a new terminal. From now on, every folder you `cd` into is covered —
the hook lives in your shell, not in any repo, with per-command repo/branch
awareness from git. Pause anytime with `export SECOND_THOUGHT_OFF=1`.

For real judgment instead of rehearsal, add one API key (free):
`console.typesafe.ai → Settings → Keys`, then store it in your Mac Keychain —
never in a file:

```sh
security add-generic-password -s second-thought-jev -a "$USER" -w
```

Without a key you get a deterministic 12-scenario mock: great for demos,
honest about its limits, and labeled as rehearsal everywhere it appears.

## A normal day with it on

Most commands pass silently — everyday ones resolve in about a millisecond without
touching the network. When something gets flagged, it looks like this:

```text
$ git push --force origin main
Warning — this looks risky. STOP — this overwrites work your whole team shares.
```

A warning still runs; it's a senior tapping your shoulder. A block doesn't run at
all. If you're sure — really sure, folder/branch/database-name checked — type
`YES` and it runs exactly once. Two rules that keep the seatbelt working: warnings
are stop-signs, not speed bumps, and **YES is not muscle memory**. Typing it blind
builds a one-word self-destruct.

Everything judged lands in a local diary (`second-thought diary`), plain words
with timestamps — your audit trail for "what happened Friday."

## Using it from scripts and AI agents

`check` never executes anything, exits 0/1/2, and appends a structured receipt —
that's a pre-tool-call gate primitive. Gate an agent's shell tool on it:

```python
import json, subprocess
p = subprocess.run(["second-thought", "check", "--live", cmd],
                   capture_output=True, text=True)
if p.returncode == 2:
    refuse("blocked", cmd)          # high-confidence destructive
elif p.returncode == 1:
    escalate_to_human(cmd)          # uncertain — a person decides
else:
    rec = json.loads(open("drill/receipt.jsonl").readline().strip())
    if rec.get("degraded"):         # live failed → mock judged
        escalate_to_human(cmd)      # never fail open for agents
    else:
        run_tool(cmd)
```

Budget math: ~70–900ms and ~$0.000001–0.00002 per check, so 1,000 gated tool
calls cost a few cents; boring commands resolve locally for $0.

## How it works

```
typed command → normalize → redact → boring? (allow, $0)
  → build_state (~400 tokens: cmd+cwd+repo+branch+history)
  → judge: live Jev (noul+choice+score, one parallel call) or mock
  → confidence gate → block/warn/allow → JSONL receipt
```

Details worth knowing: secrets are redacted *before* judging, logging, or
sending (and the judge is told a secret was hidden, so it doesn't hedge on the
marker). Gates sit at P>0.85 + confidence>0.8 + risk≥1 for block, P>0.6 for
warn — tuned for precision and deliberately never fitted to a handful of
samples. Any shell operator (`; | & $ \` > <`, newlines) forces full judgment,
so `ls; rm -rf /` can't hide behind `ls`. The hook wraps zsh's accept-line
(preexec alone can't block): a block clears the input buffer, `YES` restores it
once via an unguessable temp file. And yes — we learned the hard way that a
bare `YES` with nothing pending must never execute, because on macOS it
resolves to `/usr/bin/yes` and floods the terminal. It's guarded.

Verified by a 19-test stdlib suite (`python -m unittest discover -s tests -t .`,
also in CI on 3.11+3.14), the 12-scenario drill, and interactive shell tests of
the hook covering block, override, guard, and passthrough. Live draws vary run
to run — near-gate disagreements are calibration working, not bugs. Contributing
agents should read [`AGENTS.md`](AGENTS.md) first (mock-first rule: never spend
live API budget in automation).

## CLI reference

| Job | Does |
|---|---|
| `test` (`doctor`) | Self-test: gates, key status, latency. $0 |
| `demo` (`reel`) | Runs `drill/disasters.json`, prints scored table |
| `check "cmd"` | Judge one string. `--live` uses real Jev (needs key) |
| `diary [-n]` / `clean` | Read / rotate the local receipt log |
| `setup [--write]` / `remove` | Install / remove the shell hook (asks first) |

Verdicts are traffic-light colored on terminals, plain when piped.
`NO_COLOR=1` or `SECOND_THOUGHT_COLOR=never` forces plain.

## FAQ

**Will it slow down my shell?** Everyday commands resolve locally in ~1ms.
Scary ones take one judgment call (~70–900ms live). You'll feel nothing on
`ls`; you'll feel a beat on `rm -rf` — that's the point.

**Does it phone home?** Only live judgments leave the laptop, carrying the
redacted command plus folder/repo/branch context. Keyless mode makes zero
network calls. Ever.

**What if it blocks something legitimate?** That's what `YES` is for — once,
deliberately. If it happens often, the gates may be wrong for your workflow;
open an issue with the receipt line.

**bash/fish/Windows?** zsh on macOS today. The engine is plain Python and
portable; the hook is the zsh-specific part.

**What do you do with my data?** Nothing — there is no server side. Receipts
live in `drill/receipt.jsonl` on your disk; `clean` rotates them.

## Layout

`second_thought/` engine · `hooks/` shell glue · `tests/` suite ·
`drill/` scenarios · `docs/` beginner guide + build spec.

## License

MIT — see [LICENSE](LICENSE).

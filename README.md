# Second Thought ⏱️

Terminal seatbelt: judges each shell command **before** it runs — **allow / warn / block** (exits 0/1/2) — via Jev, a TypeSafe System One model that returns calibrated decisions instead of text, so it can't inject commands back. Stdlib-only Python, zsh hook, fail-open everywhere.

Keyless mode runs a deterministic 12-scenario mock: **rehearsal, not protection.**

- **Junior dev?** → [Why you need this](#for-junior-engineers) (5 min)
- **Senior?** → [Guarantees & rollout](#for-senior-engineers)
- **Guarding AI agents?** → [Pre-tool-call gate](#for-agent-operators)
- **New to terminals?** → [`docs/BEGINNERS.md`](docs/BEGINNERS.md) · **Coding agent?** → [`AGENTS.md`](AGENTS.md)

## Quickstart

```sh
pip install -e .              # or just use ./second-thought, no install needed
second-thought test           # self-test, $0, nothing runs
second-thought demo           # 12-scenario drill, $0, nothing runs
second-thought check "rm -rf /"  # judge one string, never executes it
```

Protection mode (key recommended) — install once, it follows you to every folder:

```sh
second-thought setup --write  # one line into ~/.zshrc (backup first), then open a new shell
export SECOND_THOUGHT_OFF=1   # pause for this shell · second-thought remove # uninstall
```

API key (for the real judge): create one at `console.typesafe.ai → Settings → Keys`,
then `security add-generic-password -s second-thought-jev -a "$USER" -w` (macOS Keychain —
never a file). Scary commands cost ~$0.00002 each; boring ones are $0.

## For junior engineers

Every team has these stories: `rm -rf` one folder too high, a database command
meant for localhost hitting prod, `git push --force main` wiping an afternoon,
a pasted `curl | bash` nobody vetted, a leaked AWS key. One command, seconds,
permanent. Reviews, CI, and backups help *around* the moment — nothing watches
the moment your finger hits Enter. That's this tool: a seatbelt, not a
replacement for backups, least-privilege, or access controls.

The hook lives in your shell, not in any repo, so one install covers every
codebase folder you'll ever `cd` into — with per-command repo/branch awareness
from git. Daily rules: green means go, **yellow means stop and read** (ask
someone if you don't understand the warning), red means it didn't run. `YES`
re-runs a block exactly once — it is not muscle memory; typing it blind builds
a one-word self-destruct.

## For senior engineers

**Pipeline:** `normalize → redact → boring? (allow, $0) → build_state (~400 tokens:
cmd+cwd+repo+branch+history) → judge: live Jev (noul+choice+score, one parallel
call) or mock → confidence gate → block/warn/allow → JSONL receipt.`

**Guarantees worth reviewing:** fail-open on every path (offline/slow/no-key
degrades to allow and records `degraded: true`, never silent); secrets redacted
*before* judging, logging, or sending, with the fact-of-redaction passed to the
judge; gates at P>0.85 + conf>0.8 + risk≥1 for block, P>0.6 warn — tuned for
precision, deliberately not fitted to samples; any shell operator forces full
judgment (`ls; rm -rf /` can't hide); bare `YES` with nothing pending can never
execute (on macOS bare `YES` resolves to `/usr/bin/yes` — guarded).

**Verification:** 19-test stdlib suite (`python -m unittest discover -s tests -t .`,
CI on 3.11+3.14), 12-scenario drill, plus interactive PTY tests of the hook
(block/override/guard/passthrough) run during development. Live draws vary run
to run — treat near-gate disagreements as calibration working, not bugs.

**Rollout:** per-dev install, key in each dev's Keychain, ~$0.003 covers a heavy
demo day. Recommend pairing with the juniors' rules above and a shared
understanding that warnings are stop-signs.

## For agent operators

`check` is a pre-tool-call gate primitive: it never executes, exits
0/1/2, and appends a structured receipt. Gate your agent's shell tool on it:

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

Budget math: ~70–900ms and ~$0.000001–0.00002 per check; 1,000 gated tool
calls ≈ a few cents. Boring commands resolve locally for $0. The receipt log
(`drill/receipt.jsonl`, `degraded`/`confidence`/`mode` fields) doubles as your
audit trail — which decision, how sure, which judge.

## CLI

| Job | Does |
|---|---|
| `test` (`doctor`) | Self-test: gates, key status, latency. $0 |
| `demo` (`reel`) | Runs `drill/disasters.json`, prints scored table |
| `check "cmd"` | Judge one string. `--live` uses real Jev (needs key) |
| `diary [-n]` / `clean` | Read / rotate the local receipt log |
| `setup [--write]` / `remove` | Install / remove the shell hook (asks first) |

Verdicts are traffic-light colored (red stop · yellow warn · green pass) on
terminals; plain text when piped. `NO_COLOR=1` or `SECOND_THOUGHT_COLOR=never`
forces plain, `=always` forces color.

## Tests

```sh
python -m unittest discover -s tests -t .   # 19 tests, milliseconds, $0, no key needed
```

## Layout

`second_thought/` engine (`filter` → `jev` → `policy` → `receipt` → `cli`) ·
`hooks/second-thought.zsh` shell glue · `tests/` suite · `drill/` scenarios ·
`docs/` beginner guide + build spec · `video/` demo shot list.

## Known limitations (honest)

- Keyless mock knows 12 scenarios; everything else waves through by design.
- Live draws vary run to run; gates are tuned for precision (block only when sure), so near-calls surface as warnings.
- A seatbelt, not a replacement for backups, least-privilege, or prod access controls.

## License

MIT — see [LICENSE](LICENSE).

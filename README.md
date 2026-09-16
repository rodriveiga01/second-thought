# Second Thought ⏱️

Terminal seatbelt: judges each shell command **before** it runs — **allow / warn / block** (exits 0/1/2) — via Jev, a TypeSafe System One model that returns calibrated decisions instead of text, so it can't inject commands back. Stdlib-only Python, zsh hook, fail-open everywhere.

Keyless mode runs a deterministic 11-scenario mock: **rehearsal, not protection.**
First time in a terminal? Start with [`docs/BEGINNERS.md`](docs/BEGINNERS.md). Coding agent? Read [`AGENTS.md`](AGENTS.md).

## Quickstart

```sh
pip install -e .          # or just use ./second-thought, no install needed
second-thought test       # self-test, $0, nothing runs
second-thought demo       # 11-scenario drill, $0, nothing runs
second-thought check "rm -rf /"  # judge one string, never executes it
```

Protection mode (key recommended):

```sh
timecop setup --write     # one line into ~/.zshrc (backup first), then open a new shell
export SECOND_THOUGHT_OFF=1      # pause for this shell · timecop remove # uninstall
```

API key (for the real judge): create one at `console.typesafe.ai → Settings → Keys`,
then `security add-generic-password -s second-thought-jev -a "$USER" -w` (macOS Keychain —
never a file). Scary commands cost ~$0.00002 each; boring ones are $0.

## How it works

```
typed command → normalize → redact → boring? (allow, $0)
  → build_state (~400 tokens: cmd+cwd+repo+branch+history)
  → judge: live Jev (noul+choice+score in one parallel call) or mock
  → confidence gate → block/warn/allow → JSONL receipt
```

The hook wraps zsh's accept-line (preexec alone can't block): block clears the
input buffer, `YES` restores it exactly once via an `mktemp` marker. Any shell
operator (`; | & $ \` > <`, newlines) forces full judgment — `ls; rm -rf /`
can't hide behind `ls`. Offline/slow/no-key degrades to allow and says so
(`degraded: true` in the receipt, never silent).

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
python -m unittest discover -s tests -t .   # 13 tests, milliseconds, $0, no key needed
```

## Layout

`second_thought/` engine (`filter` → `jev` → `policy` → `receipt` → `cli`) ·
`hooks/second-thought.zsh` shell glue · `tests/` suite · `reel/` drill ·
`docs/` beginner guide + build spec · `video/` demo shot list.

## Known limitations (honest)

- Keyless mock knows 11 scenarios; everything else waves through by design.
- Live draws vary run to run; gates are tuned for precision (block only when sure), so near-calls surface as warnings.
- A seatbelt, not a replacement for backups, least-privilege, or prod access controls.

## License

MIT — see [LICENSE](LICENSE).

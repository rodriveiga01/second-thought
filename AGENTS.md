# AGENTS.md — working in this repo (humans and coding agents)

TimeCop is a terminal seatbelt: a zsh accept-line hook judges each command
before it runs — allow/warn/block (exits 0/1/2) via Jev (TypeSafe System One
model) or a deterministic mock when keyless.

## Layout

- `timecop/` — the engine. `filter.py` (normalize/redact/allowlist) →
  `jev.py` (live client + mock) → `policy.py` (confidence gates, pre-written
  messages) → `receipt.py` (append-only JSONL log) → `cli.py` (jobs).
- `hooks/timecop.zsh` — shell glue. Accept-line wrapper (preexec alone can't
  block). Fail-open everywhere.
- `tests/` — stdlib unittest suite. Run it before and after every change.
- `reel/disasters.json` — 11-scenario drill (labels + expected verdicts).
- `docs/` — beginner guide + build spec. `.next/` is a FOREIGN project cache.
  Never read, touch, commit, or delete it.

## Commands

- `python -m unittest discover -s tests -t .` — full suite, milliseconds, $0.
- `./timecop-cli test` (aka `doctor`) — self-test. `./timecop-cli demo`
  (aka `reel`) — drill. Both never execute anything.
- `./timecop-cli check "..."` — judge one string. Never executes it either.
- Only `setup --write` / `remove` / `clean` mutate anything (shell rc / logs).

## Hard rules

1. **Mock-first, always.** Never use `--live` in scripts, loops, tests, or CI.
   It spends a real API budget and needs a Keychain key CI doesn't have
   (falls back to `degraded: true` mock). Live calls are for deliberate,
   single, human-approved checks only.
2. **Never print, log, or commit secrets.** Redact before log/send
   (`filter.redact`), keep the `redacted != norm` state note, keep receipt
   markers single. The real key lives in macOS Keychain, never in this repo —
   verify with `rg 'apikey_' .` (must be empty) before any commit.
3. **Stdlib only, Python ≥3.10.** No new dependencies without asking.
4. **Hook/filter parity.** `filter.has_ops`/`is_boring` and the shell
   `_timecop_boring` fast-path must agree: any operator forces full judgment;
   first-word matching only. Change one, change both, extend the tests.
5. **Don't tune gates to samples.** Block needs P>0.85 + conf>0.8 + risk≥1;
   warn at P>0.6. Live draws vary run to run — recalibration needs dozens of
   labeled calls, never 2–3 anecdotes.
6. **Keep outputs beginner-readable.** Short sentences, no unexplained jargon,
   every error suggests the fix. README stays programmer-concise;
   tutorial content goes in `docs/BEGINNERS.md`.
7. **Receipt logs are runtime state** (`reel/receipt*.jsonl`, gitignored).
   Never assert on them in tests; clear them with `clean`, not deletion debates.

## Architecture (30 seconds)

```
typed command → normalize → redact → boring? (allow, $0)
  → build_state (cmd+cwd+repo+branch+history, ~400 tokens)
  → judge: live Jev (noul+choice+score, parallel) or mock
  → policy gate → block/warn/allow → JSONL receipt
hook: accept-line → python check --live → block clears BUFFER,
  YES restores once via mktemp marker, TIMECOP_OFF=1 pauses.
```

Keyless mode knows 11 scenarios by heart and waves through the rest —
rehearsal, not protection. That boundary is documented and intentional.

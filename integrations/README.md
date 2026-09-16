# Pre-tool-use gate for AI coding agents

`integrations/shell-gate.sh` judges a shell command before an agent runs it.
The matching pattern in every coding tool: intercept the shell call, run one
command, allow or block on its verdict.

## Claude Code

Save `shell-gate.sh` somewhere stable and point a PreToolUse hook at it:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [{ "type": "command",
                    "command": "/absolute/path/to/shell-gate.sh" }] }
    ]
  }
}
```

- Exit **2** + reason on stderr → command never reaches the shell.
- Exit **0** → runs. Warnings print to the transcript for the agent to read.
- Garbage input, missing binary, dead network → exit 0 with a note. A broken
  gate must never wedge your agent at 3am.
- The override hint is stripped from block reasons: the blocked party is
  never taught the override word.

Same idea ports anywhere a shell call can be intercepted first: Codex,
Cursor, OpenCode, or a hand-rolled harness (`check --json` prints the full
receipt to stdout — no log file to chase, no text to parse).

## Budget

~70–900ms and ~$0.000001–0.00002 per check, so 1,000 gated tool calls cost a
few cents; boring commands resolve locally for $0. Never fail open for
agents: if the receipt says `degraded` (live failed, mock judged), escalate
to a human instead of running.

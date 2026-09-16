#!/bin/bash
# shell-gate.sh — pre-tool-use gate for AI coding agents.
#
# Reads a hook payload on stdin, judges tool_input.command with
# Second Thought, and exits 2 to block (Claude Code honors that).
# Anything else exits 0: warnings print to stderr for the transcript,
# and every failure mode fails OPEN — a broken gate must never wedge
# your agent at 3am. Needs `second-thought` on PATH (absolute path in
# your hook config is safest).
#
# Claude Code (~/.claude/settings.json):
#   {"hooks": {"PreToolUse": [{"matcher": "Bash",
#     "hooks": [{"type": "command",
#                "command": "/absolute/path/to/shell-gate.sh"}]}]}}
set -u

input=$(cat)
cmd=$(printf '%s' "$input" | python3 -c \
  "import json,sys
try:
    print(json.load(sys.stdin).get('tool_input', {}).get('command', ''))
except Exception:
    print('')" 2>/dev/null)
[ -z "$cmd" ] && exit 0

out=$(second-thought check --live "$cmd" 2>&1)
code=$?
if [ "$code" -eq 127 ]; then
  echo "shell-gate: second-thought not on PATH, allowing (fail-open)" >&2
  exit 0
fi
if [ "$code" -eq 2 ]; then
  echo "Second Thought blocked this shell command:" >&2
  # Strip the human YES-override hint: the blocked party must never be
  # taught the override word. (It wouldn't work non-interactively anyway.)
  printf '%s\n' "$out" | grep -v 'YES + Enter' >&2
  exit 2
fi
if [ "$code" -eq 1 ]; then
  echo "$out" >&2
fi
exit 0

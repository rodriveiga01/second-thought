# Second Thought shell glue — loaded into your terminal by one line in ~/.zshrc.
# Install: ./second-thought setup --write   (adds that line for you, with backup)
# Fail-open: any error -> command runs. Boring commands skip python (~1ms).

# Repo root = parent of this file's directory; works from any folder.
# (If the folder was moved or deleted, this stays empty and the terminal
#  works exactly as before — Second Thought can never break your shell.)
_second_thought_src="${(%):-%N}"
SECOND_THOUGHT_DIR="${SECOND_THOUGHT_DIR:-${_second_thought_src:A:h:h}}"
if [[ -d "$SECOND_THOUGHT_DIR/second_thought" ]]; then
  export PYTHONPATH="$SECOND_THOUGHT_DIR:$PYTHONPATH"
fi
_second_thought_marker=""
# Drop stale markers from dead shells (only our patterns; -f stays silent).
rm -f "${TMPDIR:-/tmp}"/second-thought-allow-* "${TMPDIR:-/tmp}"/timecop-allow-* 2>/dev/null || true

autoload -Uz add-zsh-hook 2>/dev/null || true
setopt BRACKETED_PASTE 2>/dev/null || true

# One-time key notice at shell start (not per-Enter). Skip when paused.
if [[ "${SECOND_THOUGHT_OFF:-}" != "1" && -z "${TYPESAFE_API_KEY:-}" ]]; then
  if ! security find-generic-password -s second-thought-jev -w >/dev/null 2>&1; then
    echo "second-thought: no API key — running demo rules. Get one: console.typesafe.ai/settings/keys, then: export TYPESAFE_API_KEY=..."
  fi
fi

# Shell-level fast path mirrors filter.has_ops/is_boring/is_own_tool
# (python is source of truth). Operators force the full check; our own
# invocations skip by PREFIX only, so `rm -rf / # second-thought` is judged.
_second_thought_boring() {
  case "$1" in
    *";"*|*"|"*|*"&"*|*'$'*|*'`'*|*">"*|*"<"*|*$'\n'*) return 1;;
  esac
  case "$1" in
    ""|"ls"|"ls "*|"cd"|"cd "*|"pwd"|"echo"|"echo "*|"cat"|"cat "*|\
    "git status"|"git status "*|"git diff --stat"|"git diff --stat "*|"git log"|"git log "*|"whoami"|"date") return 0;;
  esac
  return 1
}

_second_thought_own_tool() {
  case "$1" in
    ./second-thought|./second-thought\ *|second-thought|second-thought\ *|python3\ -m\ second_thought*|python\ -m\ second_thought*) return 0;;
  esac
  return 1
}

_second_thought_run_check() {
  local buf="$1"
  [[ -z "${buf// /}" ]] && return 0
  case "$buf" in
    *TYPESAFE_API_KEY*) return 0;;
  esac
  _second_thought_own_tool "$buf" && return 0
  _second_thought_boring "$buf" && return 0
  local repo="" branch=""
  # One git call, not two.
  local top
  top=$(git rev-parse --show-toplevel --abbrev-ref HEAD 2>/dev/null)
  if [[ -n "$top" ]]; then
    branch="${top##*$'\n'}"
    repo=$(basename "${top%$'\n'*}")
  fi
  local out
  out=$(python3 -m second_thought.cli check --live --cwd "$PWD" --repo "$repo" --branch "$branch" "$buf" 2>/dev/null)
  local code=$?
  if [[ $code -eq 2 ]]; then
    # Unpredictable per-block file: no fixed path to race or trick.
    _second_thought_marker="$(mktemp "${TMPDIR:-/tmp}/second-thought-allow-XXXXXX" 2>/dev/null)" || _second_thought_marker=""
    if [[ -n "$_second_thought_marker" ]]; then
      print -r -- "$buf" > "$_second_thought_marker"
    fi
    zle -M "$out"
    BUFFER=""
    return 1
  elif [[ $code -eq 1 ]]; then
    zle -M "$out (executing)"
  fi
  return 0
}

second-thought-accept-line() {
  # Paused? Run everything untouched. (Pause: export SECOND_THOUGHT_OFF=1)
  if [[ "${SECOND_THOUGHT_OFF:-}" == "1" ]]; then
    zle .accept-line
    return
  fi
  # YES override: restore blocked command, run it unchecked exactly once.
  # Guard first: a bare YES with nothing pending must NEVER execute — on
  # macOS (case-insensitive FS) YES resolves to /usr/bin/yes and floods
  # the terminal with infinite output. Seen in the wild; hence this guard.
  if [[ "$BUFFER" == "YES" ]]; then
    if [[ -n "${_second_thought_marker:-}" && -s "$_second_thought_marker" ]]; then
      BUFFER="$(<"$_second_thought_marker")"
      rm -f "$_second_thought_marker"
      _second_thought_marker=""
      zle .accept-line
    else
      zle -M "Nothing to unblock — YES only works right after a block."
      BUFFER=""
    fi
    return
  fi
  # Any other command voids a pending YES.
  [[ -n "${_second_thought_marker:-}" ]] && rm -f "$_second_thought_marker"
  _second_thought_marker=""
  _second_thought_run_check "$BUFFER" || return
  zle .accept-line
}
zle -N accept-line second-thought-accept-line 2>/dev/null || true

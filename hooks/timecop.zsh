# TimeCop shell glue — loaded into your terminal by one line in ~/.zshrc.
# Install: ./timecop-cli setup --write   (adds that line for you, with backup)
# Fail-open: any error -> command runs. Boring commands skip python (~1ms).

# Repo root = parent of this file's directory; works from any folder.
# (If the folder was moved or deleted, this stays empty and the terminal
#  works exactly as before — TimeCop can never break your shell.)
_timecop_src="${(%):-%N}"
TIMECOP_DIR="${TIMECOP_DIR:-${_timecop_src:A:h:h}}"
if [[ -d "$TIMECOP_DIR/timecop" ]]; then
  export PYTHONPATH="$TIMECOP_DIR:$PYTHONPATH"
fi
_timecop_marker=""
# Drop stale markers from dead shells (only our pattern; -f stays silent).
rm -f "${TMPDIR:-/tmp}"/timecop-allow-* 2>/dev/null || true

autoload -Uz add-zsh-hook 2>/dev/null || true
setopt BRACKETED_PASTE 2>/dev/null || true

# One-time key notice at shell start (not per-Enter). Skip when paused.
if [[ "${TIMECOP_OFF:-}" != "1" && -z "${TYPESAFE_API_KEY:-}" ]]; then
  if ! security find-generic-password -s timecop-jev -w >/dev/null 2>&1; then
    echo "timecop: no API key — running demo rules. Get one: console.typesafe.ai/settings/keys, then: export TYPESAFE_API_KEY=..."
  fi
fi

# Shell-level fast path mirrors filter.py SAFE_PREFIXES (python is source of truth).
# First rule mirrors has_ops(): any shell operator forces the full check,
# so `ls; rm -rf /` can never sneak through on its first two letters.
_timecop_boring() {
  case "$1" in
    *";"*|*"|"*|*"&"*|*'$'*|*'`'*|*">"*|*"<"*|*$'\n'*) return 1;;
  esac
  case "$1" in
    ""|"ls"|"ls "*|"cd"|"cd "*|"pwd"|"echo"|"echo "*|"cat"|"cat "*|\
    "git status"|"git status "*|"git diff --stat"|"git diff --stat "*|"git log"|"git log "*|"whoami"|"date") return 0;;
  esac
  return 1
}

_timecop_run_check() {
  local buf="$1"
  [[ -z "${buf// /}" ]] && return 0
  case "$buf" in
    *timecop*|*TYPESAFE_API_KEY*) return 0;;
  esac
  _timecop_boring "$buf" && return 0
  local repo="" branch=""
  # One git call, not two.
  local top
  top=$(git rev-parse --show-toplevel --abbrev-ref HEAD 2>/dev/null)
  if [[ -n "$top" ]]; then
    branch="${top##*$'\n'}"
    repo=$(basename "${top%$'\n'*}")
  fi
  local out
  out=$(python3 -m timecop.cli check --live --cwd "$PWD" --repo "$repo" --branch "$branch" "$buf" 2>/dev/null)
  local code=$?
  if [[ $code -eq 2 ]]; then
    # Unpredictable per-block file: no fixed path to race or trick.
    _timecop_marker="$(mktemp "${TMPDIR:-/tmp}/timecop-allow-XXXXXX" 2>/dev/null)" || _timecop_marker=""
    if [[ -n "$_timecop_marker" ]]; then
      print -r -- "$buf" > "$_timecop_marker"
    fi
    zle -M "$out"
    BUFFER=""
    return 1
  elif [[ $code -eq 1 ]]; then
    zle -M "$out (executing)"
  fi
  return 0
}

timecop-accept-line() {
  # Paused? Run everything untouched. (Pause: export TIMECOP_OFF=1)
  if [[ "${TIMECOP_OFF:-}" == "1" ]]; then
    zle .accept-line
    return
  fi
  # YES override: restore blocked command, run it unchecked exactly once.
  if [[ "$BUFFER" == "YES" && -n "${_timecop_marker:-}" && -s "$_timecop_marker" ]]; then
    BUFFER="$(<"$_timecop_marker")"
    rm -f "$_timecop_marker"
    _timecop_marker=""
    zle .accept-line
    return
  fi
  # Any other command voids a pending YES.
  [[ -n "${_timecop_marker:-}" ]] && rm -f "$_timecop_marker"
  _timecop_marker=""
  _timecop_run_check "$BUFFER" || return
  zle .accept-line
}
zle -N accept-line timecop-accept-line 2>/dev/null || true

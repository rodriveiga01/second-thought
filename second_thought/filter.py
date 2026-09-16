"""Local-first filter: normalize, allowlist boring cmds, redact secrets.

Nothing here touches the network. Goal: 90% of keystrokes cost $0 / 0ms.
"""

import base64
import re

ZERO_WIDTH = re.compile(r"[\u200b-\u200d\ufeff]")
SAFE_WORDS = ("ls", "cd", "pwd", "echo", "cat", "whoami", "date")
SAFE_PHRASES = ("git status", "git diff --stat", "git log")

# Judging our own invocations is meaningless — and the inner quoted evil
# would false-positive (`second-thought check "rm -rf /"` contains rm -rf).
# PREFIX ONLY: `rm -rf / # second-thought` must still be judged.
# Mirrored by the shell fast-path in hooks/second-thought.zsh.
OWN_PREFIXES = ("./second-thought", "second-thought",
                "python3 -m second_thought.cli", "python -m second_thought.cli")


def is_own_tool(cmd: str) -> bool:
    s = (cmd or "").strip().lower()
    return any(s == p or s.startswith(p + " ") for p in OWN_PREFIXES)

SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED-AWS-KEY]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{10,}"), "[REDACTED-GITHUB-TOKEN]"),
    (re.compile(r"xox[bap]-[A-Za-z0-9-]+"), "[REDACTED-SLACK-TOKEN]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "[REDACTED-PRIVATE-KEY]"),
    (re.compile(r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*\S+"),
     r"\1=[REDACTED]"),
    (re.compile(r"export\s+\w*(SECRET|PASSWORD|TOKEN|KEY)\w*=\S+"),
     "export CREDENTIAL=[REDACTED]"),
]


def normalize(cmd: str) -> str:
    """Strip invisible chars, expand common evasions for analysis only."""
    clean = ZERO_WIDTH.sub("", cmd or "")
    clean = clean.replace("${IFS}", " ")
    try:  # \x76 -> v, \n -> newline: decode escape sequences for analysis
        clean = re.sub(r"\\x([0-9a-fA-F]{2})",
                       lambda m: chr(int(m.group(1), 16)), clean)
    except Exception:
        pass
    # If `echo <blob> | base64 -d` pattern, surface decoded text for judging.
    if "base64" in clean and "-d" in clean:
        for tok in re.findall(r"[A-Za-z0-9+/=]{20,}", clean):
            try:
                decoded = base64.b64decode(tok + "=" * (-len(tok) % 4)).decode(
                    "utf-8", "ignore")
                if decoded.strip():
                    clean += f"\n[decoded-b64:{decoded[:200]}]"
                    break
            except Exception:
                continue
    return clean


# Any shell operator means "more than one thing happens" — never boring,
# no matter what the command starts with (`ls; rm -rf /` starts with ls).
# Keep in sync with _timecop_boring() in hooks/timecop.zsh.
SHELL_OPS = (";", "|", "&", "$", "`", "\n", ">", "<")


def has_ops(cmd: str) -> bool:
    return any(op in (cmd or "") for op in SHELL_OPS)


def _starts_word(s: str, prefix: str) -> bool:
    return s == prefix or s.startswith(prefix + " ")


def is_boring(cmd: str) -> bool:
    s = (cmd or "").strip()
    if not s:
        return True
    if has_ops(s):
        return False
    low = s.lower()
    # Whole first word, not prefix: `lsof` is not `ls`, `datebook` is not `date`.
    if low.split(None, 1)[0] in SAFE_WORDS:
        return True
    return any(_starts_word(low, p) for p in SAFE_PHRASES)


def redact(cmd: str) -> str:
    out = cmd or ""
    for pat, repl in SECRET_PATTERNS:
        out = pat.sub(repl, out)
    return out


def build_state(cmd: str, cwd: str = "", repo: str = "", branch: str = "",
                ssh_host: str = "", last_cmds: "list[str] | None" = None,
                script_head: str = "") -> str:
    """Tiny structured note for Jev. Keep ~300-500 tokens."""
    lines = (script_head or "").splitlines()[:40]
    hist = (last_cmds or [])[-3:]
    parts = [
        f"command: {(cmd or '')[:1000]}",
        f"cwd: {cwd or '(unknown)'}",
        f"repo: {repo or '(unknown)'} branch: {branch or '(unknown)'}",
        f"ssh_host: {ssh_host or '(local)'}",
        f"recent: {' | '.join(hist) if hist else '(none)'}",
    ]
    if lines:
        parts.append("script_head:\n" + "\n".join(lines)[:2000])
    return "\n".join(parts)

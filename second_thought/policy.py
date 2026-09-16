"""Confidence-gated policy. Jev votes, code decides. Messages pre-written."""

BLOCK_P = 0.85
BLOCK_CONF = 0.8
WARN_P = 0.6

MESSAGES = {
    # Plain words on purpose: these are shown to people who never coded.
    # The YES hint is added by the caller (shell/CLI), not here.
    "evil-paste": "STOP — this installs unknown software as an administrator. It could wipe your files or spy on you.",
    "nuke-prod": "STOP — this deletes files permanently. There is no undo.",
    "leak-secret": "STOP — this would upload a secret password/key where others can see it.",
    "team-nuke": "STOP — this overwrites work your whole team shares.",
    "ai-lie": "STOP — this 'cleanup' command actually deletes your home folder.",
}


def decide(danger_p: float, confidence: float, disaster: str,
           risk: float) -> tuple[str, str]:
    """Returns (action, message). action in {allow, warn, block}."""
    severe = disaster in MESSAGES and risk >= 1.0
    if severe and danger_p >= BLOCK_P and confidence >= BLOCK_CONF:
        return "block", MESSAGES[disaster]
    if danger_p >= WARN_P:
        label = MESSAGES.get(disaster, "")
        if label:
            return "warn", f"Warning — this looks risky. {label}"
        return "warn", "Warning — this looks risky, but it doesn't match a known disaster pattern."
    return "allow", ""

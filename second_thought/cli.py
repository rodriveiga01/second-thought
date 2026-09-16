"""Second Thought: looks at a terminal command BEFORE it runs and stops dangerous ones.

Safe to try: test, demo and check NEVER run commands — they only print
opinions, like reading a recipe instead of cooking the meal.
New here? Read README.md first, or double-click "Start Here.command".
"""

import argparse
import difflib
import json
import os
import sys
import time

from . import filter as F
from . import jev
from . import policy
from . import receipt

EXIT = {"allow": 0, "warn": 1, "block": 2}
# Traffic light: 0 = green (fine), 1 = yellow (warning, carried on),
# 2 = red (stopped on purpose). The shell connector needs three different
# numbers, which is why "blocked" is 2 and not 1. None of them mean "crashed".

COLORS = {"red": "31", "yellow": "33", "green": "32"}


def use_color():
    """Verdict colors only. Auto-off when piped, dumb terminal, or NO_COLOR;
    SECOND_THOUGHT_COLOR=always|never overrides. (Note: the shell hook shows
    plain text regardless — zle -M strips ANSI codes.)"""
    force = os.environ.get("SECOND_THOUGHT_COLOR", "").lower()
    if force == "always":
        return True
    if force in ("never", "no", "0"):
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def paint(text, color, enabled):
    if not enabled or color not in COLORS:
        return text
    return f"\033[{COLORS[color]}m{text}\033[0m"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECEIPT_PATH = os.path.join(ROOT, "drill", "receipt.jsonl")
ARCHIVE_PATH = os.path.join(ROOT, "drill", "receipt-archive.jsonl")
HOOK_LINE_MARK = "hooks/second-thought.zsh"

# Friendly nicknames (same jobs, easier words). All still work.
ALIASES = {"test": "doctor", "demo": "reel", "setup": "init",
           "remove": "uninstall"}
JOBS = ["check", "reel", "init", "doctor", "uninstall", "clean", "diary"]


class FriendlyParser(argparse.ArgumentParser):
    """Same errors as normal, plus a plain-English hint."""

    def error(self, message):
        import re
        hint = ("New here? Each command needs a JOB (a task word): "
                "test, demo, check, setup, or remove.\n"
                "Easiest first step: run the self-test with the job 'test'.\n"
                "Full guide: README.md (or double-click 'Start Here.command').\n")
        m = re.search(r"invalid choice: '([^']+)'", message)
        if m:
            hint = f"I don't know the job '{m.group(1)}'.{_suggest(m.group(1))} " + hint
        elif "unrecognized arguments" in message:
            hint = ("That usually means a command with spaces wasn't put in quotes. "
                    "Quotes glue it into one piece: check \"rm -rf /\" — "
                    "without quotes the pieces scatter and I can't tell what you meant. " + hint)
        elif "required: job" in message or "required: command" in message:
            hint = ("It looks like a word is missing. " + hint)
        # Show friendly names first; twins in parentheses so nothing looks secret.
        message = re.sub(r"\(choose from [^)]*\)",
                         "(choose from 'test', 'demo', 'check', 'setup', 'remove', "
                         "'diary', 'clean' — older twins also work: doctor, reel, init, uninstall)",
                         message)
        super().print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: {message}\n" + hint)


def _suggest(job: str) -> str:
    near = difflib.get_close_matches(job, JOBS + list(ALIASES), n=1)
    if near:
        return f" Did you mean '{near[0]}'?"
    return ""


def check(cmd: str, live: bool = False, cwd="", repo="", branch="",
          ssh_host="", last=None, script_head="") -> dict:
    t0 = time.time()
    stamp = time.strftime("%Y-%m-%d %H:%M")
    norm = F.normalize(cmd)
    redacted = F.redact(norm)
    if F.is_own_tool(norm):
        return {"action": "allow", "reason": "own-tool", "cost_usd": 0.0,
                "ms": int((time.time() - t0) * 1000), "cmd": redacted[:200],
                "mode": "local", "message": "", "key": "n/a", "at": stamp,
                "degraded": False}
    if F.is_boring(norm):
        return {"action": "allow", "reason": "allowlist", "cost_usd": 0.0,
                "ms": int((time.time() - t0) * 1000), "cmd": redacted[:200],
                "mode": "local", "message": "", "key": "n/a", "at": stamp,
                "degraded": False}
    state = F.build_state(redacted, cwd, repo, branch, ssh_host, last, script_head)
    if redacted != norm:
        # Redaction hides the secret but must not hide the FACT a secret was
        # present — otherwise the judge sees "[REDACTED]" and hedges.
        state += "\nredaction: a password/key/secret was hidden in the command before judging."
    used_live = False
    key_status = "n/a"
    if live:
        key = jev.get_key()
        if key:
            key_status = "ok"
            j = jev.live_judge(state, key)
            used_live = j is not None
        else:
            key_status = "missing"
            j = None
    else:
        j = None
    if not used_live:
        j = jev.mock_judge(state)
    # Live asked but mock served (no key / timeout / offline): say so.
    # Silent fallback would lie about what protected you.
    degraded = bool(live and not used_live)
    action, msg = policy.decide(j["danger_p"], j["confidence"], j["disaster"], j["risk"])
    usage = j.get("usage", {}) if used_live else {}
    # Rough cost: $0.042 per million input pieces. Tokens unknown here; estimate len/4.
    est_tokens = max(1, len(state) // 4)
    cost = (est_tokens / 1e6) * 0.042 if used_live else 0.0
    return {"action": action, "message": msg, "judge": j, "cost_usd": round(cost, 6),
            "ms": int((time.time() - t0) * 1000), "cmd": redacted[:200],
            "usage": usage, "mode": "live" if used_live else "dry-run",
            "key": key_status, "at": stamp, "degraded": degraded}


def _hook_line() -> str:
    return f'source "{ROOT}/hooks/second-thought.zsh"  # second-thought'


def _zshrc() -> str:
    return os.path.expanduser("~/.zshrc")


def cmd_init(write: bool) -> int:
    key = jev.get_key()
    print("Second Thought setup — 4 steps. Nothing changes until step 4, and step 4 saves a backup first.")
    print(f'1. Shell connector: {_hook_line()}')
    print("   (One line in your terminal's settings file loads Second Thought into each new terminal.)")
    print(f"2. Python: {sys.version.split()[0]} — good.")
    if key:
        print("3. AI key: found. Real-AI protection is available.")
    else:
        print("3. AI key: not added yet — that's fine, the free built-in rules ($0) work without it.")
        print("   To add it later: console.typesafe.ai → sign in → Settings → Keys →")
        print("   create a key, then run: security add-generic-password -s second-thought-jev -a \"$USER\" -w")
        print("   (A box will ask for the key — paste it there. It never touches your typed history.)")
    print("4. Self-test: ./second-thought test")
    if write:
        line = _hook_line()
        cur = open(_zshrc(), encoding="utf-8").read() if os.path.exists(_zshrc()) else ""
        if HOOK_LINE_MARK in cur:
            print("Done: that line is already there. Nothing added. Restart the terminal to use it.")
        else:
            bak = _zshrc() + ".bak"
            open(bak, "w", encoding="utf-8").write(cur)
            with open(_zshrc(), "a", encoding="utf-8") as f:
                f.write(f"\n{line}\n")
            print(f"Done: added one line to the settings file (backup saved at {bak} — you'll see it in your home folder).")
            print("Restart the terminal. Pause anytime with: export SECOND_THOUGHT_OFF=1")
    else:
        print("Tip: re-run with --write and I'll add the line from step 1 for you (with backup).")
    return 0


def cmd_uninstall(a) -> int:
    if not os.path.exists(_zshrc()):
        print("No terminal settings file found — Second Thought was never turned on, nothing to remove.")
        return 0
    lines = open(_zshrc(), encoding="utf-8").read().splitlines()
    kept = [ln for ln in lines if HOOK_LINE_MARK not in ln]
    if len(kept) == len(lines):
        print("You're already off — Second Thought was never connected to this terminal, so there's nothing to undo.")
        return 0
    if not a.yes:
        try:
            ans = input("Remove the one Second Thought line from ~/.zshrc? [y/N] ").strip().lower()
        except EOFError:
            ans = ""
        if ans not in ("y", "yes"):
            print("Kept as-is. Nothing changed.")
            return 0
    bak = _zshrc() + ".bak"
    open(bak, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    open(_zshrc(), "w", encoding="utf-8").write("\n".join(kept) + "\n")
    print(f"Removed. (Backup saved at {bak}. Restart the terminal.)")
    return 0


def cmd_doctor() -> int:
    print("Second Thought self-test — SAFE: this only reads words and prints opinions. Nothing runs. Cost $0.")
    t0 = time.time()
    r1 = check("ls -la")
    r2 = check("sudo rm -rf /")
    r3 = check("git push --force origin main", cwd="/work/monorepo",
               repo="monorepo", branch="main")
    key = jev.get_key()
    on = use_color()
    g1 = r1["action"] == "allow"
    g2 = r2["action"] == "block"
    g3 = r3["action"] == "block"
    ok, bad = paint("[PASS]", "green", on), paint("[FAIL]", "red", on)
    print(f"{ok if g1 else bad} Everyday command recognized (\"ls\" waves through)")
    print(f"{ok if g2 else bad} Mass-delete stopped (\"sudo rm -rf /\" would be blocked — it was NOT run)")
    print(f"{ok if g3 else bad} Shared-work overwrite stopped (\"git push --force main\" would be blocked — it was NOT run)")
    if key:
        print(f"{ok} AI key: found. Real-AI protection is available.")
    else:
        print(f"{paint('[NOTE]', 'yellow', on)} No AI key — the free built-in rules are active ($0).")
        print("       NOTE means 'one optional thing missing', not 'you failed'.")
        print("       Add a key for real AI protection (README step 6).")
    print(f"Done in about {int((time.time() - t0) * 1000)}ms (ms = milliseconds, thousandths of a second).")
    print("Verdict: " + ("Second Thought works. The only thing that changed: a few diary lines "
                          "(drill/receipt.jsonl). Nothing else on your computer was touched."
                          if (g1 and g2 and g3) else "something is wrong — ask for help."))
    return 0 if (g1 and g2 and g3) else 1


def cmd_check(a) -> int:
    text = (a.command or "").strip()
    if not text:
        print("You gave me an empty command — nothing to judge. "
              "Try: ./second-thought check \"ls\"")
        return 0
    if text.upper() == "YES":
        print("Note: the word YES by itself is harmless, so this says OK. "
              "YES is only magic in a protected terminal right after something "
              "was blocked — there it re-runs that blocked command once. "
              "Here in 'check' there is nothing to unblock.")
        return 0
    if a.live and not jev.get_key():
        print("Note: you asked for the real AI (--live) but no AI key was found, "
              "so I used the free built-in rules instead. Nothing was spent. "
              "(README step 6 to add a key.)", file=sys.stderr)
    rec = check(a.command, live=a.live, cwd=a.cwd, repo=a.repo,
                branch=a.branch, ssh_host=a.ssh_host)
    receipt.append(RECEIPT_PATH, rec)
    if a.json:
        print(json.dumps(rec))
        return EXIT[rec["action"]]
    on = use_color()
    if rec["action"] == "allow":
        print(paint("OK — looks safe. ($0.00, instant.)", "green", on))
    elif rec["action"] == "warn":
        print(paint(rec["message"], "yellow", on))
        print("Heads-up only — in a protected terminal this would still run. "
              "(\"check\" itself never runs anything.)")
    else:
        print(paint(rec["message"], "red", on))
        print("In a protected terminal: type YES + Enter to run it once. "
              "(\"check\" itself never runs anything. Blocked-on-purpose shows as exit 2, not a crash.)")
    return EXIT[rec["action"]]


def cmd_reel(a) -> int:
    with open(a.file, encoding="utf-8") as f:
        cases = json.load(f)
    print(f"Second Thought safety drill — {len(cases)} famous bad commands as TEXT ONLY (like reading about fires in a textbook). Nothing runs.")
    if a.live and not jev.get_key():
        print("Note: you asked for the real AI (--live) but no AI key was found, "
              "so this drill used the free built-in rules. Nothing was spent.", file=sys.stderr)
    n_block = n_warn = n_allow = 0
    cost = 0.0
    on = use_color()
    for case in cases:
        rec = check(case["cmd"], live=a.live, cwd=case.get("cwd", ""),
                    repo=case.get("repo", ""), branch=case.get("branch", ""),
                    ssh_host=case.get("ssh_host", ""))
        receipt.append(RECEIPT_PATH, rec)
        cost += rec["cost_usd"]
        n_block += rec["action"] == "block"
        n_warn += rec["action"] == "warn"
        n_allow += rec["action"] == "allow"
        label = case.get("label", case["id"])
        verb = {"block": "stopped", "warn": "warning shown", "allow": "allowed"}[rec["action"]]
        if rec["action"] == case.get("expect"):
            print(f'{paint("[PASS]", "green", on)} {label} → {verb} as expected '
                  f'({"built-in rules" if rec["mode"] != "live" else "real AI"})')
        else:
            print(f'{paint("[FAIL]", "red", on)} {label} → {verb} (wanted: {case.get("expect")}). Worth a look.')
    mode = "real AI" if a.live and jev.get_key() else "built-in rules"
    print(f"Result: {n_block} stopped, {n_warn} warning shown, {n_allow} allowed. "
          f"Cost ${cost:.2f} ({mode}).")
    return 0


def cmd_clean() -> int:
    n = 0
    if os.path.exists(RECEIPT_PATH):
        with open(RECEIPT_PATH, encoding="utf-8") as f:
            lines = f.readlines()
        n = len(lines)
        if n:
            with open(ARCHIVE_PATH, "a", encoding="utf-8") as f:
                f.writelines(lines)
        open(RECEIPT_PATH, "w", encoding="utf-8").write("")
    print(f"Cleared the diary ({n} lines moved to receipt-archive.jsonl). Fresh start.")
    print("The attic file is safe to delete whenever you like.")
    return 0


def cmd_diary(a) -> int:
    if not os.path.exists(RECEIPT_PATH):
        print("Diary is empty — run the self-test first: ./second-thought test")
        return 0
    with open(RECEIPT_PATH, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    if not lines:
        print("Diary is empty — run the self-test first: ./second-thought test")
        return 0
    shown = lines[-a.n:]
    print(f"Diary — last {len(shown)} checks (plain words; full details stay in drill/receipt.jsonl):")
    for ln in shown:
        try:
            r = json.loads(ln)
        except json.JSONDecodeError:
            continue
        when = r.get("at", "—")
        cmd = (r.get("cmd") or "")[:70]
        action = r.get("action", "?")
        on = use_color()
        if action == "block":
            what = paint("STOPPED", "red", on)
        elif action == "warn":
            what = paint("warning shown", "yellow", on)
        else:
            what = paint("allowed", "green", on)
        judge = r.get("judge", {}) or {}
        sure = ""
        if isinstance(judge, dict) and "danger_p" in judge:
            sure = f", {int(round(judge['danger_p'] * 100))}% sure"
        mode = "real AI" if r.get("mode") == "live" else "built-in rules"
        if r.get("degraded"):
            mode += " — live unavailable"
        print(f"  {when} — {what} '{cmd}'{sure} ({mode})")
    return 0


def main(argv=None) -> int:
    p = FriendlyParser(
        prog="second-thought",
        description="Looks at a terminal command BEFORE it runs and stops dangerous ones. "
                    "Safe to try: test, demo and check never run commands — they only print opinions.",
        epilog="New here? Read README.md first, or double-click 'Start Here.command'. "
               "First step: ./second-thought test")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="job",
                           help="the task word: test (self-test), demo (safety drill), "
                                "check (judge one command), setup (turn protection on), "
                                "remove (turn it off again)")
    c = sub.add_parser("check", help="judge one command you type in quotes (never runs it)",
                       aliases=[])
    c.add_argument("command", help="the command to judge, in quotes so multi-word commands stay together. Only read, never run.")
    c.add_argument("--live", action="store_true",
                   help="use the real AI over the internet (needs AI key; fractions of a cent; "
                        "without a key it uses the free built-in rules instead)")
    c.add_argument("--json", action="store_true",
                   help="print the full receipt as JSON (for scripts and agent harnesses)")
    c.add_argument("--cwd", default="", help=argparse.SUPPRESS)
    c.add_argument("--repo", default="", help=argparse.SUPPRESS)
    c.add_argument("--branch", default="", help=argparse.SUPPRESS)
    c.add_argument("--ssh-host", default="", help=argparse.SUPPRESS)
    r = sub.add_parser("reel", aliases=["demo"],
                       help="run the safety drill: famous bad commands as text only (nothing runs)")
    r.add_argument("--live", action="store_true",
                   help="judge with the real AI (needs AI key; costs under a cent total)")
    r.add_argument("--file", default=os.path.join(ROOT, "drill", "disasters.json"),
                   help=argparse.SUPPRESS)
    i = sub.add_parser("init", aliases=["setup"], help="setup: shows 4 steps, or does step 1 for you with --write")
    i.add_argument("--write", action="store_true",
                   help="add the one connector line to the terminal settings file (backup made first)")
    sub.add_parser("doctor", aliases=["test"], help="self-test: proves it works. $0, nothing runs, nothing changes.")
    un = sub.add_parser("uninstall", aliases=["remove"], help="disconnect from the terminal (asks first, backup made)")
    un.add_argument("--yes", action="store_true", help="skip the confirmation question")
    sub.add_parser("clean", help="clear the diary file (old lines are kept in receipt-archive.jsonl)")
    d = sub.add_parser("diary", help="read the diary in plain words (newest last)")
    d.add_argument("-n", type=int, default=10, help="how many recent checks to show (default: 10)")
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        argv = ["test"]  # bare launcher runs the safest useful thing: the self-test
    a = p.parse_args(argv)
    job = ALIASES.get(a.cmd, a.cmd)  # 'demo' → 'reel', 'test' → 'doctor', etc.
    if job == "init":
        return cmd_init(a.write)
    if job == "doctor":
        return cmd_doctor()
    if job == "check":
        return cmd_check(a)
    if job == "reel":
        return cmd_reel(a)
    if job == "uninstall":
        return cmd_uninstall(a)
    if job == "clean":
        return cmd_clean()
    if job == "diary":
        return cmd_diary(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())

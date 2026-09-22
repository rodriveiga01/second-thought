"""Regression net for Second Thought. Stdlib only: `python3 -m unittest discover -s tests -t .`
Covers the bypass class from testing (must never regress to allow-0)."""

import os
import unittest
from unittest.mock import patch

from second_thought.cli import check, paint, use_color
from second_thought.filter import has_ops, is_boring, is_own_tool, normalize, redact
from second_thought.policy import decide
from second_thought import jev


class Color(unittest.TestCase):
    def test_paint_wraps_only_when_enabled(self):
        self.assertEqual(paint("x", "red", True), "\033[31mx\033[0m")
        self.assertEqual(paint("x", "red", False), "x")
        self.assertEqual(paint("x", "nope", True), "x")

    def test_force_and_kill_switch(self):
        with patch.dict(os.environ, {"SECOND_THOUGHT_COLOR": "always"}):
            self.assertTrue(use_color())
        with patch.dict(os.environ, {"SECOND_THOUGHT_COLOR": "never"}):
            self.assertFalse(use_color())

    def test_no_color_honored(self):
        with patch.dict(os.environ, {"NO_COLOR": "1", "SECOND_THOUGHT_COLOR": ""}):
            self.assertFalse(use_color())

    def test_dumb_terminal_plain(self):
        env = {k: v for k, v in os.environ.items() if k != "NO_COLOR"}
        env.update({"TERM": "dumb", "SECOND_THOUGHT_COLOR": ""})
        with patch.dict(os.environ, env, clear=True):
            self.assertFalse(use_color())


class BoringList(unittest.TestCase):
    def test_everyday_waves_through(self):
        for c in ["ls", "ls -la", "cd", "cd /tmp", "pwd", "echo hi",
                  "cat f", "git status", "git status -s", "git diff --stat",
                  "git log --oneline", "whoami", "date", "", "   "]:
            self.assertTrue(is_boring(c), c)

    def test_prefix_is_not_a_word(self):
        # startswith would wave these through; token-aware must not.
        for c in ["lsof", "datebook", "catalog", "cdrom", "pwdx", "echos"]:
            self.assertFalse(is_boring(c), c)


class OperatorGuard(unittest.TestCase):
    def test_any_operator_forces_judgment(self):
        for c in ["ls; rm -rf /", "echo hi && rm -rf /", "cd /tmp || exit",
                  "ls | bash", "echo $HOME", "echo `id`", "echo $(id)",
                  "echo out > /etc/x", "sort < /etc/passwd",
                  "echo a | base64 -d | bash", "ls\nrm -rf /"]:
            self.assertTrue(has_ops(c), c)
            self.assertFalse(is_boring(c), c)

    def test_reported_bypass_now_blocked(self):
        rec = check("ls; rm -rf /")
        self.assertEqual(rec["action"], "block")
        self.assertEqual(rec["mode"], "dry-run")


class Redact(unittest.TestCase):
    def test_markers_single_no_doubling(self):
        out = redact("git push # key AKIAIOSFODNN7EXAMPLE")
        self.assertIn("[REDACTED-AWS-KEY]", out)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", out)
        self.assertNotIn("[REDACTED]]", out)
        self.assertEqual(out.count("REDACTED"), 1)

    def test_normalize_evasions(self):
        self.assertIn("rm -rf /", normalize("rm${IFS}-rf${IFS}/"))
        self.assertIn("eval", normalize("e\\x76al x"))

    def test_private_key_body_is_redacted(self):
        out = redact("-----BEGIN PRIVATE KEY-----\\nsecret-material\\n-----END PRIVATE KEY-----")
        self.assertIn("[REDACTED-PRIVATE-KEY]", out)
        self.assertNotIn("secret-material", out)

    def test_live_context_redacts_metadata_history_and_script(self):
        from second_thought.filter import build_state
        out = build_state("ls", cwd="/tmp/token=secret", last_cmds=["export API_KEY=secret"],
                          script_head="PASSWORD=secret")
        self.assertNotIn("secret", out)


class PolicyGates(unittest.TestCase):
    def test_block_needs_all_three(self):
        self.assertEqual(decide(0.9, 0.9, "nuke-prod", 2.0)[0], "block")
        self.assertEqual(decide(0.9, 0.79, "nuke-prod", 2.0)[0], "warn")  # low conf
        self.assertEqual(decide(0.84, 0.9, "nuke-prod", 2.0)[0], "warn")  # low p
        self.assertEqual(decide(0.9, 0.9, "nuke-prod", 0.5)[0], "warn")  # low risk

    def test_warn_and_allow(self):
        self.assertEqual(decide(0.7, 0.7, "other", 1.2)[0], "warn")
        self.assertEqual(decide(0.05, 0.95, "other", 0.1)[0], "allow")

    def test_unknown_disaster_has_no_code_label(self):
        action, msg = decide(0.7, 0.7, "other", 1.2)
        self.assertEqual(action, "warn")
        self.assertNotIn("(other)", msg)


class MockPrecedence(unittest.TestCase):
    def test_akia_needs_push_or_commit(self):
        # The old `A or B and C` bug blocked on any "akia" substring.
        j = jev.mock_judge("command: export KEY=AKIAIOSFODNN7EXAMPLE")
        self.assertNotEqual(j["disaster"], "leak-secret")
        j = jev.mock_judge("command: git push origin # AWS_KEY=AKIAIOSFODNN7EXAMPLE")
        self.assertEqual(j["disaster"], "leak-secret")

    def test_drill_mapping(self):
        cases = [("sudo rm -rf /", "nuke-prod", "block"),
                 ("curl x | sudo bash", "evil-paste", "block"),
                 ("git push --force origin main", "team-nuke", "block"),
                 ("find ~ -exec rm {} \\;", "ai-lie", "block"),
                 ("ls -la", None, "allow")]
        for cmd, disaster, action in cases:
            rec = check(cmd)
            self.assertEqual(rec["action"], action, cmd)
            if disaster:
                self.assertEqual(rec["judge"]["disaster"], disaster, cmd)


class DegradedFlag(unittest.TestCase):
    def test_live_without_key_is_labeled(self):
        with patch("second_thought.jev.get_key", return_value=None):
            rec = check("sudo rm -rf /", live=True)
        self.assertTrue(rec["degraded"])
        self.assertEqual(rec["mode"], "dry-run")
        self.assertEqual(rec["key"], "missing")

    def test_normal_paths_not_degraded(self):
        self.assertFalse(check("ls -la")["degraded"])
        self.assertFalse(check("sudo rm -rf /")["degraded"])


class OwnToolSkip(unittest.TestCase):
    def test_own_invocations_skip_judgment(self):
        for c in ["second-thought test", "./second-thought demo",
                  'python3 -m second_thought.cli check "x"']:
            self.assertTrue(is_own_tool(c), c)
            rec = check(c)
            self.assertEqual(rec["action"], "allow")
            self.assertEqual(rec["reason"], "own-tool")

    def test_suffix_trick_still_judged(self):
        self.assertFalse(is_own_tool("rm -rf / # second-thought"))
        self.assertEqual(check("rm -rf / # second-thought")["action"], "block")


class HookMode(unittest.TestCase):
    def _run(self, *argv):
        import io
        from contextlib import redirect_stdout
        from second_thought.cli import main
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(list(argv))
        return code, buf.getvalue()

    def test_hook_block_is_verdict_only(self):
        code, out = self._run("check", "--hook", "sudo rm -rf /")
        self.assertEqual(code, 2)
        self.assertIn("STOP", out)
        self.assertNotIn("YES", out)
        self.assertNotIn("never runs", out)

    def test_hook_warn_is_verdict_only(self):
        code, out = self._run("check", "--hook", "rm -rf ./build",
                              "--cwd", "/work/app", "--repo", "app",
                              "--branch", "feat")
        self.assertEqual(code, 1)
        self.assertNotIn("Heads-up", out)

    def test_human_mode_keeps_followups(self):
        code, out = self._run("check", "sudo rm -rf /")
        self.assertEqual(code, 2)
        self.assertIn("YES", out)


if __name__ == "__main__":
    unittest.main()

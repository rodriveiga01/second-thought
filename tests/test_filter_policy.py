"""Regression net for Second Thought. Stdlib only: `python3 -m unittest discover -s tests -t .`
Covers the bypass class from testing (must never regress to allow-0)."""

import unittest
from unittest.mock import patch

from second_thought.cli import check
from second_thought.filter import has_ops, is_boring, is_own_tool, normalize, redact
from second_thought.policy import decide
from second_thought import jev


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


if __name__ == "__main__":
    unittest.main()

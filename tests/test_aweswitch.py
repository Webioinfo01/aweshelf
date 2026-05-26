"""Tests for lib/aweswitch.py."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aweshelf.lib.aweswitch import (
    load_aweswitch_config,
    detect_profile,
    profile_exists,
    build_resume_command,
)


def write_config(path: Path, profiles: dict) -> None:
    data = {"profiles": profiles}
    path.write_text(json.dumps(data, indent=2))


class AweSwitchTests(unittest.TestCase):
    def test_load_aweswitch_config_not_found(self):
        result = load_aweswitch_config.__wrapped__() if hasattr(load_aweswitch_config, '__wrapped__') else None
        # Direct test with nonexistent path
        import aweshelf.lib.aweswitch as aw
        orig = aw.aweswitch_config_path
        aw.aweswitch_config_path = lambda: Path("/nonexistent/config.json")
        try:
            result = load_aweswitch_config()
            self.assertIsNone(result)
        finally:
            aw.aweswitch_config_path = orig

    def test_detect_profile_by_url(self):
        config = {
            "profiles": {
                "claude": {
                    "cc-glm": {
                        "env": {
                            "ANTHROPIC_BASE_URL": "https://api.glm.com",
                            "ANTHROPIC_MODEL": "claude-sonnet-4-20250514",
                        }
                    }
                }
            }
        }
        import aweshelf.lib.aweswitch as aw
        orig = aw.load_aweswitch_config
        aw.load_aweswitch_config = lambda: config
        try:
            result = detect_profile({"ANTHROPIC_BASE_URL": "https://api.glm.com", "ANTHROPIC_MODEL": ""})
            self.assertEqual(result, "cc-glm")
        finally:
            aw.load_aweswitch_config = orig

    def test_detect_profile_by_model(self):
        config = {
            "profiles": {
                "claude": {
                    "cc-gemini": {
                        "env": {
                            "ANTHROPIC_BASE_URL": "https://api.gemini.com",
                            "ANTHROPIC_MODEL": "gemini-pro",
                        }
                    }
                }
            }
        }
        import aweshelf.lib.aweswitch as aw
        orig = aw.load_aweswitch_config
        aw.load_aweswitch_config = lambda: config
        try:
            result = detect_profile({"ANTHROPIC_BASE_URL": "", "ANTHROPIC_MODEL": "gemini-pro"})
            self.assertEqual(result, "cc-gemini")
        finally:
            aw.load_aweswitch_config = orig

    def test_detect_profile_no_match(self):
        config = {
            "profiles": {
                "claude": {
                    "cc-glm": {
                        "env": {"ANTHROPIC_BASE_URL": "https://api.glm.com", "ANTHROPIC_MODEL": "m1"}
                    }
                }
            }
        }
        import aweshelf.lib.aweswitch as aw
        orig = aw.load_aweswitch_config
        aw.load_aweswitch_config = lambda: config
        try:
            result = detect_profile({"ANTHROPIC_BASE_URL": "https://other.com", "ANTHROPIC_MODEL": "m2"})
            self.assertIsNone(result)
        finally:
            aw.load_aweswitch_config = orig

    def test_detect_profile_empty_env(self):
        import aweshelf.lib.aweswitch as aw
        orig = aw.load_aweswitch_config
        aw.load_aweswitch_config = lambda: {"profiles": {}}
        try:
            result = detect_profile({"ANTHROPIC_BASE_URL": "", "ANTHROPIC_MODEL": ""})
            self.assertIsNone(result)
        finally:
            aw.load_aweswitch_config = orig

    def test_profile_exists_true(self):
        config = {"profiles": {"claude": {"cc-glm": {"env": {}}}}}
        import aweshelf.lib.aweswitch as aw
        orig = aw.load_aweswitch_config
        aw.load_aweswitch_config = lambda: config
        try:
            self.assertTrue(profile_exists("cc-glm"))
        finally:
            aw.load_aweswitch_config = orig

    def test_profile_exists_false(self):
        config = {"profiles": {"claude": {"cc-glm": {"env": {}}}}}
        import aweshelf.lib.aweswitch as aw
        orig = aw.load_aweswitch_config
        aw.load_aweswitch_config = lambda: config
        try:
            self.assertFalse(profile_exists("nonexistent"))
        finally:
            aw.load_aweswitch_config = orig

    def test_build_resume_command_with_profile(self):
        cmd = build_resume_command("claude", "cc-glm", "session-123")
        self.assertEqual(cmd, ["aweswitch", "cc-glm", "--resume", "session-123"])

    def test_build_resume_command_raw(self):
        cmd = build_resume_command("claude", "cc-glm", "session-123", raw=True)
        self.assertEqual(cmd, ["claude", "--resume", "session-123"])

    def test_build_resume_command_no_profile(self):
        cmd = build_resume_command("claude", None, "session-123")
        self.assertEqual(cmd, ["claude", "--resume", "session-123"])

    def test_build_resume_command_codex(self):
        cmd = build_resume_command("codex", None, "session-123")
        self.assertEqual(cmd, ["codex", "resume", "session-123"])


if __name__ == "__main__":
    unittest.main()

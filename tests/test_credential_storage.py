"""Credential storage and backup permissions regression tests."""
import os
import stat
import tempfile
import unittest
from pathlib import Path

from hermes_oauth_openai_codex.auth_json import _atomic_write
from hermes_oauth_openai_codex.planf3_env import write_env


class CredentialStorageTests(unittest.TestCase):
    def test_token_cache_is_replaced_atomically_and_private(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "auth.json"
            _atomic_write(path, '{"access_token":"first"}')
            _atomic_write(path, '{"access_token":"second"}')
            self.assertIn("second", path.read_text())
            self.assertNotIn("first", path.read_text())
            self.assertEqual(list(Path(directory).glob(".auth.json.*")), [])
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_env_and_backup_are_private_even_with_permissive_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("OPENAI_API_KEY=previous\n# keep comment\n")
            if os.name == "posix":
                path.chmod(0o644)
            write_env(path, {"OPENAI_API_KEY": "replacement"}, backup=True)
            self.assertIn("OPENAI_API_KEY=replacement", path.read_text())
            self.assertIn("# keep comment", path.read_text())
            backups = list(Path(directory).glob(".env.bak.*"))
            self.assertEqual(len(backups), 1)
            self.assertIn("previous", backups[0].read_text())
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                self.assertEqual(stat.S_IMODE(backups[0].stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()

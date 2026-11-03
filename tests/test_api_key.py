"""Offline configuration tests; no Anthropic or Vault credentials are required."""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from dotenv import load_dotenv


# The API client is not needed to test configuration. Keep the suite runnable
# with only python-dotenv installed, and never initialize a real client.
spec = importlib.util.spec_from_file_location(
    "illudumQ36", Path(__file__).resolve().parents[1] / "illudumQ36.py"
)
app = importlib.util.module_from_spec(spec)
with patch.dict("sys.modules", {"anthropic": types.ModuleType("anthropic")}):
    spec.loader.exec_module(app)


class ApiKeyTests(unittest.TestCase):
    def setUp(self):
        # Do not use any credentials or .env files from the test runner.
        self.enter_context(patch.dict(os.environ, {}, clear=True))
        directory = self.enter_context(tempfile.TemporaryDirectory())
        self.env_file = Path(directory) / ".env"
        self.enter_context(
            patch.object(app, "load_dotenv", side_effect=self.load_test_dotenv)
        )
        self.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.enter_context(
            patch("socket.socket", side_effect=AssertionError("Network not allowed"))
        )

        self.vault = Mock()
        self.vault.is_authenticated.return_value = True
        self.vault.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "fake-vault-api-key"}}
        }
        self.hvac = types.ModuleType("hvac")
        self.hvac.Client = Mock(return_value=self.vault)
        self.enter_context(patch.dict("sys.modules", {"hvac": self.hvac}))

    def enter_context(self, manager):
        # unittest.TestCase.enterContext is not available on Python 3.8.
        result = manager.__enter__()
        self.addCleanup(manager.__exit__, None, None, None)
        return result

    def load_test_dotenv(self, *args, **kwargs):
        return load_dotenv(self.env_file, *args, **kwargs)

    def write_env(self, text):
        self.env_file.write_text(text, encoding="utf-8")

    def test_direct_key_from_dotenv(self):
        self.write_env("ANTHROPIC_API_KEY=fake-dotenv-key\n")

        self.assertEqual(app.get_api_key(), "fake-dotenv-key")
        self.hvac.Client.assert_not_called()

    def test_exported_direct_key_takes_precedence(self):
        self.write_env("ANTHROPIC_API_KEY=fake-dotenv-key\n")
        os.environ["ANTHROPIC_API_KEY"] = "fake-exported-key"

        self.assertEqual(app.get_api_key(), "fake-exported-key")
        self.hvac.Client.assert_not_called()

    def test_dotenv_selects_and_configures_vault(self):
        self.write_env(
            "USE_VAULT=true\n"
            "VAULT_ADDR=https://vault.example:8200\n"
            "VAULT_TOKEN=fake-dotenv-token\n"
        )

        self.assertEqual(app.get_api_key(), "fake-vault-api-key")
        self.hvac.Client.assert_called_once_with(
            url="https://vault.example:8200", token="fake-dotenv-token"
        )
        self.vault.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="anthropic/api_key", mount_point="secret"
        )

    def test_exported_false_overrides_dotenv_vault_selection(self):
        self.write_env("USE_VAULT=true\nANTHROPIC_API_KEY=fake-dotenv-key\n")
        os.environ["USE_VAULT"] = "false"

        self.assertEqual(app.get_api_key(), "fake-dotenv-key")
        self.hvac.Client.assert_not_called()

    def test_exported_vault_configuration_takes_precedence(self):
        self.write_env(
            "USE_VAULT=false\n"
            "VAULT_ADDR=https://dotenv.example:8200\n"
            "VAULT_TOKEN=fake-dotenv-token\n"
        )
        os.environ.update(
            USE_VAULT="true",
            VAULT_ADDR="https://exported.example:8200",
            VAULT_TOKEN="fake-exported-token",
        )

        self.assertEqual(app.get_api_key(), "fake-vault-api-key")
        self.hvac.Client.assert_called_once_with(
            url="https://exported.example:8200", token="fake-exported-token"
        )

    def test_exported_vault_selection_loads_dotenv_token(self):
        self.write_env("VAULT_TOKEN=fake-dotenv-token\n")
        os.environ["USE_VAULT"] = "true"

        self.assertEqual(app.get_api_key(), "fake-vault-api-key")
        self.hvac.Client.assert_called_once_with(
            url="http://127.0.0.1:8200", token="fake-dotenv-token"
        )

    def test_vault_works_without_dotenv_and_accepts_mixed_case_true(self):
        os.environ.update(USE_VAULT="TrUe", VAULT_TOKEN="fake-exported-token")

        self.assertEqual(app.get_api_key(), "fake-vault-api-key")
        self.hvac.Client.assert_called_once_with(
            url="http://127.0.0.1:8200", token="fake-exported-token"
        )

    def test_missing_direct_key_is_reported(self):
        with self.assertRaisesRegex(ValueError, "ANTHROPIC_API_KEY not found"):
            app.get_api_key()
        self.hvac.Client.assert_not_called()

    def test_missing_vault_token_does_not_fall_back_to_direct_key(self):
        self.write_env("USE_VAULT=true\nANTHROPIC_API_KEY=fake-direct-key\n")

        with self.assertRaisesRegex(RuntimeError, "VAULT_TOKEN.*not set"):
            app.get_api_key()
        self.hvac.Client.assert_not_called()

    def test_vault_authentication_failure_does_not_fall_back(self):
        self.write_env(
            "USE_VAULT=true\nVAULT_TOKEN=fake-token\n"
            "ANTHROPIC_API_KEY=fake-direct-key\n"
        )
        self.vault.is_authenticated.return_value = False

        with self.assertRaisesRegex(RuntimeError, "Vault authentication failed"):
            app.get_api_key()
        self.vault.secrets.kv.v2.read_secret_version.assert_not_called()

    def test_vault_read_failure_does_not_fall_back(self):
        self.write_env(
            "USE_VAULT=true\nVAULT_TOKEN=fake-token\n"
            "ANTHROPIC_API_KEY=fake-direct-key\n"
        )
        self.vault.secrets.kv.v2.read_secret_version.side_effect = RuntimeError(
            "test-only read failure"
        )

        with self.assertRaisesRegex(RuntimeError, "Vault error: test-only read failure"):
            app.get_api_key()

    def test_missing_hvac_is_reported(self):
        os.environ.update(USE_VAULT="true", VAULT_TOKEN="fake-token")

        with patch.dict("sys.modules", {"hvac": None}):
            with self.assertRaisesRegex(ImportError, "pip install hvac"):
                app.get_api_key()


if __name__ == "__main__":
    unittest.main()

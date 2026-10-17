import json
import os
import pathlib
import subprocess
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "inspect_isolated_fixture.cjs"


class FixtureIsolationTests(unittest.TestCase):
    def call(self, data, patch=None):
        env = os.environ.copy()
        env.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        env.pop("FIREBASE_SERVICE_ACCOUNT", None)
        env.update(GCLOUD_PROJECT="demo-passway",
                   FIRESTORE_EMULATOR_HOST="127.0.0.1:8080",
                   FIREBASE_AUTH_EMULATOR_HOST="127.0.0.1:9099")
        env.update(patch or {})
        return subprocess.run(["node", str(SCRIPT), json.dumps(data)],
                              env=env, capture_output=True, text=True, timeout=5)

    def test_real_services_or_credentials_rejected_before_sdk_import(self):
        for patch in [{"GCLOUD_PROJECT": "real-project"},
                      {"FIRESTORE_EMULATOR_HOST": "firestore.googleapis.com"},
                      {"FIREBASE_AUTH_EMULATOR_HOST": "identitytoolkit.googleapis.com"},
                      {"GOOGLE_APPLICATION_CREDENTIALS": "/missing/test-credential.json"},
                      {"FIREBASE_SERVICE_ACCOUNT": "not-a-real-key"}]:
            with self.subTest(patch=patch):
                r = self.call({"action": "snapshot", "phones": ["9999900001"]}, patch)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("Strict fixture isolation guard failed", r.stderr)

    def test_nonfixture_phone_cannot_be_inspected(self):
        r = self.call({"action": "snapshot", "phones": ["0000000000"]})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Unsupported fixture command", r.stderr)

    def test_expiry_requires_an_explicit_owned_code(self):
        r = self.call({"action": "expire", "phones": ["9999900001"]})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Expiry requires an owned code", r.stderr)

    def test_arbitrary_admin_actions_are_not_supported(self):
        r = self.call({"action": "clear-database", "phones": ["9999900001"]})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Unsupported fixture command", r.stderr)
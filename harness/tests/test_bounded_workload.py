"""The workload must refuse cloud projects/credentials before SDK import."""
import os
import pathlib
import subprocess
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "bounded_backend_workload.cjs"


class BoundedWorkloadGuardTests(unittest.TestCase):
    def rejects(self, patch):
        env = os.environ.copy()
        env.pop("FIREBASE_SERVICE_ACCOUNT", None)
        env.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        env.update(FIRESTORE_EMULATOR_HOST="127.0.0.1:8080", GCLOUD_PROJECT="demo-passway")
        env.update(patch)
        result = subprocess.run(
            ["node", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=5
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Local demo-only guard failed", result.stderr)

    def test_remote_firestore_host_rejected(self):
        self.rejects({"FIRESTORE_EMULATOR_HOST": "example.invalid:8080"})

    def test_non_demo_project_rejected(self):
        self.rejects({"GCLOUD_PROJECT": "not-a-demo-project"})

    def test_service_account_rejected(self):
        self.rejects({"FIREBASE_SERVICE_ACCOUNT": '{"not":"a-real-credential"}'})

    def test_application_default_credentials_rejected(self):
        self.rejects({"GOOGLE_APPLICATION_CREDENTIALS": "/nonexistent/test-key.json"})
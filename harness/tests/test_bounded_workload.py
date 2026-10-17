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
class BoundedVerifiedPhoneFixtureTests(unittest.TestCase):
    def test_fixture_claims_are_valid_unique_and_bounded(self):
        source = SCRIPT.read_text()
        start = source.index('const syntheticPhone=')
        end = source.index('const call=', start)
        script = source[start:end] + """
const assert=require('node:assert/strict');
const phones=[];
for(let i=0;i<16;i++)for(const side of ['a','b'])phones.push(syntheticPhone('bounded-'+side+i));
assert.equal(new Set(phones).size,32);
for(const phone of phones)assert.match(phone,/^\\+[1-9]\\d{1,14}$/);
assert.throws(()=>syntheticPhone('production-user'),/Unknown workload fixture/);
"""
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_workload_supplies_explicit_synthetic_verified_phone_context(self):
        source = SCRIPT.read_text()
        self.assertIn('auth:{uid,token:{phone_number:syntheticPhone(uid)}}', source)
        self.assertLess(source.index('Local demo-only guard failed'), source.index('const syntheticPhone='))

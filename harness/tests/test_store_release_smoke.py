import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    'store_release_smoke', Path(__file__).resolve().parents[1] / 'store_release_smoke.py')
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


class StoreReleaseArtifactBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.apk = self.directory / 'passway-store-signed.apk'
        self.apk.write_bytes(b'PK-test-fixture')
        self.digest = hashlib.sha256(self.apk.read_bytes()).hexdigest()
        self.metadata = {'package': 'com.passway.app', 'versionCode': 8,
                         'sha256': self.digest, 'bytes': self.apk.stat().st_size}
        self.write()

    def write(self):
        (self.directory / 'download-verification.json').write_text(json.dumps(self.metadata))

    def test_exact_artifact_is_accepted_without_device_interaction(self):
        self.assertEqual(smoke.verify_download(self.directory, self.digest), self.metadata)

    def test_package_version_type_and_size_must_match(self):
        for key, value in [('package', 'other.app'), ('versionCode', 7),
                           ('versionCode', True), ('versionCode', '8'), ('bytes', 0)]:
            with self.subTest(key=key, value=value):
                original = dict(self.metadata)
                self.metadata[key] = value
                self.write()
                with self.assertRaises(ValueError):
                    smoke.verify_download(self.directory, self.digest)
                self.metadata = original
                self.write()

    def test_actual_bytes_and_metadata_cannot_replace_trusted_hash(self):
        self.apk.write_bytes(b'PK-replaced')
        self.metadata.update(sha256=hashlib.sha256(self.apk.read_bytes()).hexdigest(),
                             bytes=self.apk.stat().st_size)
        self.write()
        with self.assertRaises(ValueError):
            smoke.verify_download(self.directory, self.digest)

    def test_default_is_bound_to_verified_play_release_not_fixture(self):
        with self.assertRaises(ValueError):
            smoke.verify_download(self.directory)
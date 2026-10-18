from pathlib import Path
import importlib.util
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "configure_store_signing.py"
spec = importlib.util.spec_from_file_location("configure_store_signing", MODULE_PATH)
signing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(signing)


class SignedBuildConfigurationTests(unittest.TestCase):
    def test_plugin_eof_without_newline_is_delimited(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "build.gradle"
            path.write_text("apply plugin: 'com.google.firebase.crashlytics'")
            signing.configure(path)
            self.assertIn(
                "'com.google.firebase.crashlytics'\n\n// PASSWAY_STORE_SIGNING\n",
                path.read_text(),
            )

    def test_existing_newline_and_duplicate_application_are_safe(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "build.gradle"
            path.write_text("android {}\n")
            signing.configure(path)
            self.assertEqual(path.read_text().count(signing.MARKER), 1)
            with self.assertRaises(ValueError):
                signing.configure(path)

    def test_signing_fragment_references_private_files_not_embedded_credentials(self):
        self.assertIn("System.getenv('PASSWAY_SIGNING_JSON')", signing.FRAGMENT)
        self.assertIn("System.getenv('PASSWAY_KEYSTORE_PATH')", signing.FRAGMENT)
        self.assertNotIn("println", signing.FRAGMENT)
        self.assertNotIn("keystoreBase64", signing.FRAGMENT)
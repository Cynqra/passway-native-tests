import copy
import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location(
    "release_metadata", pathlib.Path(__file__).resolve().parents[1] / "release_metadata.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReleaseMetadataTests(unittest.TestCase):
    def setUp(self):
        self.config = {"android": {"package": "com.passway.app", "versionCode": 7},
                       "version": "0.3.1"}
        self.provenance = {"sourceRepository": "naveenbharti310/Paasway",
                           "sourceCommit": "a" * 40, "archiveSha256": "b" * 64}

    def test_source_and_version_are_bound_without_copying_other_config(self):
        self.config["secret_not_for_artifact"] = "fixture"
        result = module.metadata(self.config, self.provenance)
        self.assertEqual(result["versionCode"], 7)
        self.assertEqual(result["sourceCommit"], "a" * 40)
        self.assertNotIn("secret_not_for_artifact", result)

    def test_future_versions_do_not_require_workflow_edits(self):
        self.config["android"]["versionCode"] = 8
        self.config["version"] = "0.3.2"
        self.assertEqual(module.metadata(self.config, self.provenance)["versionCode"], 8)

    def test_invalid_versions_and_packages_are_rejected(self):
        for code in [0, -1, "7", True, 2100000001]:
            with self.subTest(code=code):
                self.config["android"]["versionCode"] = code
                with self.assertRaises(ValueError):
                    module.metadata(self.config, self.provenance)
        self.config["android"] = {"package": "different.app", "versionCode": 7}
        with self.assertRaises(ValueError):
            module.metadata(self.config, self.provenance)

    def test_invalid_source_bindings_are_rejected(self):
        for field, value in [("sourceRepository", "other/repo"),
                             ("sourceCommit", "main"), ("archiveSha256", "bad")]:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.provenance)
                bad[field] = value
                with self.assertRaises(ValueError):
                    module.metadata(self.config, bad)

    def test_non_release_version_names_are_rejected(self):
        for value in ["", None, "latest", "0.3.1\nuntrusted"]:
            with self.subTest(version=value):
                self.config["version"] = value
                with self.assertRaises(ValueError):
                    module.metadata(self.config, self.provenance)
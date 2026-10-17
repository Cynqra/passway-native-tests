import json
import pathlib
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
import play_prelaunch_script as m


class PrelaunchScriptTests(unittest.TestCase):
    def config(self):
        return {"project": "passway-2ddc8", "fixtures": [
            {"phone": "+919999900001", "code": "246810"},
            {"phone": "+919999900002", "code": "135790"}]}

    def test_only_reserved_fictional_phones(self):
        for phone in ["+919876543210", "+919999900003", "", None]:
            config = self.config()
            config["fixtures"][0]["phone"] = phone
            with self.assertRaises(ValueError):
                m.build(config)

    def test_rejects_wrong_project_and_duplicate_accounts(self):
        config = self.config()
        config["project"] = "another-project"
        with self.assertRaises(ValueError):
            m.build(config)
        config = self.config()
        config["fixtures"][1] = config["fixtures"][0]
        with self.assertRaises(ValueError):
            m.build(config)

    def test_rejects_missing_or_non_string_codes(self):
        for code in [None, 246810, "", "12345", "1234567", "abcdef", "１２３４５６"]:
            config = self.config()
            config["fixtures"][0]["code"] = code
            with self.assertRaises(ValueError):
                m.build(config)

    def test_supported_conditional_bounded_events_without_undocumented_optional(self):
        scripts = m.build(self.config())
        self.assertEqual(len(scripts), 10)
        self.assertEqual(len({s["id"] for s in scripts}), len(scripts))
        allowed = {"VIEW_CLICKED", "VIEW_TEXT_CHANGED", "WAIT_FOR_ELEMENT",
                   "WAIT", "ASSERTION", "ELEMENT_SCROLL_INTO_VIEW", "ELEMENT_IGNORED"}
        for script in scripts:
            self.assertIn("contextDescriptor", script)
            if script["id"] != 1699:
                self.assertLessEqual(script["maxNumberOfRuns"], 3)
            for action in script["actions"]:
                self.assertIn(action["eventType"], allowed)
                self.assertNotIn("optional", action)
                if "delayTime" in action:
                    self.assertLessEqual(action["delayTime"], 30000)

    def test_consent_scrolled_then_explicitly_accepted(self):
        script = next(s for s in m.build(self.config()) if s["id"] == 1605)
        # "Passway use rules" also appears as a public document link on login.
        # That link must not trigger a premature consent-screen script.
        self.assertNotEqual(script["contextDescriptor"]["elementDescriptors"],
                            [{"text": "Passway use rules"}])
        self.assertIn("Read and accept these rules",
                      script["contextDescriptor"]["elementDescriptors"][0]["text"])
        self.assertEqual(script["actions"][0]["eventType"], "ELEMENT_SCROLL_INTO_VIEW")
        self.assertEqual(script["actions"][0]["childElementDescriptors"],
                         m.descriptor("accept-use-rules"))
        self.assertEqual(script["actions"][1], m.click("accept-use-rules"))
        self.assertEqual(script["actions"][-1], m.assertion("generate"))

    def test_no_external_peer_seeded_chat_or_production_bypass(self):
        text = json.dumps(m.build(self.config()))
        for forbidden in ["connectionId", "chat-row-", "Synthetic peer acknowledgement",
                          "ADB_SHELL_COMMAND", "appCheckDebugToken", "http://", "https://"]:
            self.assertNotIn(forbidden, text)
        finish = next(s for s in m.build(self.config()) if s["id"] == 1608)
        self.assertIn(m.click("cancel-code"), finish["actions"])
        self.assertEqual(finish["actions"][-1], m.assertion("settings-name"))

    def test_permissions_are_not_blocked_by_wait_inside_generate(self):
        scripts = m.build(self.config())
        generate = next(s for s in scripts if s["id"] == 1606)
        permission = next(s for s in scripts if s["id"] == 1607)
        self.assertFalse(any(a["eventType"] == "WAIT_FOR_ELEMENT" for a in generate["actions"]))
        self.assertGreater(permission["priority"], generate["priority"])

    def test_script_identifiers_exist_in_exact_release_source_archive(self):
        root = pathlib.Path(__file__).resolve().parents[2]
        with tarfile.open(root / "validation/architecture-source.tar.gz") as archive:
            source = "\n".join(
                archive.extractfile(member).read().decode()
                for member in archive.getmembers()
                if member.isfile() and member.name.endswith(".tsx"))
        for name in ["welcome-next", "get-started", "phone-input", "send-code",
                     "verify-input", "verify", "age-day", "age-month", "age-year",
                     "age-continue", "accept-use-rules", "generate", "name-input",
                     "cancel-code", "code-text", "open-settings", "settings-name"]:
            self.assertTrue(bool(re.search(r"['\"]" + re.escape(name) + r"['\"]", source)), name)

    def test_private_output_and_no_stdout_credentials_or_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            fixture = root / "fixtures.json"
            output = root / "crawl.json"
            fixture.write_text(json.dumps(self.config()))
            command = [sys.executable, m.__file__, str(fixture), str(output)]
            completed = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            for secret in ["+919999900001", "+919999900002", "246810", "135790"]:
                self.assertNotIn(secret, completed.stdout + completed.stderr)
            original = output.read_bytes()
            repeated = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(output.read_bytes(), original)
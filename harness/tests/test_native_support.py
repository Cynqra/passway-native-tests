import importlib.util
import pathlib
import sys
import types
import xml.etree.ElementTree as ET
import unittest
from contextlib import contextmanager
from unittest import mock

FILE = pathlib.Path(__file__).resolve().parents[1] / "native_support_journey.py"


@contextmanager
def noop_deadline(_seconds):
    yield


def load(resolver="No activity found", user="0", activity="mResumedActivity: external.mail/.Composer", foreground="external.mail"):
    calls, checks = [], []
    def shell(*args):
        calls.append(args)
        if args == ("am", "get-current-user"):
            return user
        if args[:2] == ("cmd", "package"):
            return resolver
        return activity
    def waitfor(selector, _seconds):
        calls.append(("wait", selector))
        return {"text": "Email support at Limerencetechnologies@gmail.com." if selector == "support-error" else "Limerencetechnologies@gmail.com"}
    driver = types.SimpleNamespace(
        dump=lambda _label="current": ET.fromstring('<hierarchy><node package="'+foreground+'" visible-to-user="true" text="Welcome" /></hierarchy>'),
        shell=shell, tap=lambda value: calls.append(("tap", value)),
        waitfor=waitfor, find=lambda _s: {"enabled": "true"},
        back=lambda: calls.append(("back",)), deadline=noop_deadline,
        remaining_timeout=lambda _seconds: (_ for _ in ()).throw(TimeoutError("bounded handoff")),
    )
    spec = importlib.util.spec_from_file_location("native_support_under_test", FILE)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"driver": driver}):
        spec.loader.exec_module(module)
    return module, calls, checks


class NativeSupportTests(unittest.TestCase):
    def run_support(self, module, checks):
        module.verify_support({"check": lambda name, ok: checks.append((name, ok)), "snap": lambda _label: None})

    def test_missing_mail_client_checks_native_fallback_and_address(self):
        module, calls, checks = load()
        self.run_support(module, checks)
        self.assertEqual(len(checks), 3)
        self.assertTrue(all(ok for _, ok in checks))
        self.assertIn(("wait", "support-error"), calls)
        self.assertNotIn(("back",), calls)

    def test_existing_client_requires_foreground_handoff_and_returns(self):
        module, calls, checks = load("external.mail/.Composer")
        self.run_support(module, checks)
        self.assertIn(("back",), calls)
        self.assertEqual(len(checks), 3)

    def test_resolver_alone_is_not_native_handoff_proof(self):
        module, calls, checks = load("external.mail/.Composer", activity="mResumedActivity: com.passway.app/.MainActivity", foreground="com.passway.app")
        with self.assertRaises(TimeoutError):
            self.run_support(module, checks)
        self.assertFalse(checks)

    def test_unrelated_foreground_app_is_not_mail_handoff_proof(self):
        module, calls, checks = load("external.mail/.Composer", activity="mResumedActivity: unrelated.launcher/.Home", foreground="unrelated.launcher")
        with self.assertRaises(TimeoutError):
            self.run_support(module, checks)
        self.assertFalse(checks)

    def test_actual_mail_ui_is_proof_without_legacy_activity_field(self):
        module, calls, checks = load("com.google.android.gm/.ComposeActivityGmail", activity="topResumedActivity: different field", foreground="com.google.android.gm")
        self.run_support(module, checks)
        self.assertTrue(all(ok for _, ok in checks))
        self.assertFalse(any(args[:1] == ("dumpsys",) for args in calls))

    def test_activity_claim_cannot_override_wrong_visible_package(self):
        module, calls, checks = load("external.mail/.Composer", foreground="unrelated.launcher")
        with self.assertRaises(TimeoutError):
            self.run_support(module, checks)
        self.assertFalse(checks)

    def test_unknown_resolver_fails_before_dispatch(self):
        module, calls, checks = load("Unknown command")
        with self.assertRaises(RuntimeError):
            self.run_support(module, checks)
        self.assertFalse(any(args[0] == "tap" for args in calls))

    def test_unknown_user_fails_before_dispatch(self):
        module, calls, checks = load(user="not-a-user")
        with self.assertRaises(RuntimeError):
            self.run_support(module, checks)
        self.assertFalse(any(args[0] == "tap" for args in calls))

    def test_support_intent_never_adds_private_data_or_send_action(self):
        module, calls, checks = load()
        self.run_support(module, checks)
        resolver = next(args for args in calls if args[:2] == ("cmd", "package"))
        self.assertEqual(resolver[-1], "mailto:Limerencetechnologies@gmail.com")
        self.assertFalse(any("send" == str(part).lower() for args in calls for part in args))
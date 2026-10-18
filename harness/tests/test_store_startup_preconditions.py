import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

SPEC = importlib.util.spec_from_file_location(
    'store_release_smoke_preflight',
    Path(__file__).resolve().parents[1] / 'store_release_smoke.py')
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)

MODAL = "Something went wrong. Check that Google Play is enabled on your device"
WRONG_INSTALLER = "LicenseClient: Local install check failed due to wrong installer"
OLD_SERVICES = (
    "Google Play services out of date for com.passway.app. "
    "Requires 261200000 but found 242335041")


class StartupPreconditionTests(unittest.TestCase):
    def test_observed_license_blocker_is_classified_without_disabling_security(self):
        result = smoke.classify_startup_blocker(MODAL, WRONG_INSTALLER + "\n" + OLD_SERVICES)
        self.assertEqual(result['kind'], 'environment-blocked')
        self.assertEqual(result['signals'], ['wrong-installer', 'play-services-outdated'])
        self.assertFalse(result['passed'])
        self.assertFalse(result['storeInstallationOrAttestationVerified'])

    def test_no_classification_from_generic_app_error_or_old_unrelated_log(self):
        for text, logs in [("Something went wrong. Try again.", WRONG_INSTALLER),
                           (MODAL, "FATAL EXCEPTION: main"),
                           ("Welcome", WRONG_INSTALLER),
                           (MODAL, "")]:
            with self.subTest(text=text, logs=logs):
                self.assertIsNone(smoke.classify_startup_blocker(text, logs))

    def test_only_numeric_older_services_are_classified(self):
        for found in ('261200000', '271200000', 'unknown'):
            self.assertIsNone(smoke.classify_startup_blocker(
                MODAL, OLD_SERVICES.replace('242335041', found)))

    def test_detailed_licensing_denial_is_not_a_success(self):
        result = smoke.classify_startup_blocker(
            MODAL, "com.pairip.licensecheck.LicenseCheckException: "
            "Licensing service could not process request")
        self.assertEqual(result['signals'], ['licensing-service-denied'])
        self.assertFalse(result['passed'])

    def test_environment_blocker_stops_on_first_fresh_snapshot(self):
        tree = ET.fromstring('<hierarchy><node text="' + MODAL + '"/></hierarchy>')
        calls = []
        def read():
            calls.append('read')
            return tree
        with self.assertRaises(smoke.StartupEnvironmentBlocked):
            smoke.wait_for_release_onboarding(
                read, lambda *args: None, lambda: WRONG_INSTALLER,
                sleep_fn=lambda seconds: self.fail("Must not retry a known blocker"))
        self.assertEqual(calls, ['read'])

    def test_expected_control_returns_without_reading_logs(self):
        control = {'visible-to-user': 'true'}
        result = smoke.wait_for_release_onboarding(
            lambda: ET.fromstring('<hierarchy/>'), lambda *args: control,
            lambda: self.fail("No log lookup needed on successful startup"))
        self.assertEqual(result, control)

    def test_unknown_failure_is_bounded_not_reclassified_as_pass(self):
        ticks = iter([0, 0, 2])
        with self.assertRaises(TimeoutError):
            smoke.wait_for_release_onboarding(
                lambda: ET.fromstring('<hierarchy><node text="Unknown"/></hierarchy>'),
                lambda *args: None, lambda: "",
                seconds=1, clock=lambda: next(ticks), sleep_fn=lambda _: None)

    def test_precondition_logs_remain_credential_free_structured_metadata(self):
        result = smoke.classify_startup_blocker(MODAL, WRONG_INSTALLER + "\nSECRET_SENTINEL")
        self.assertNotIn('SECRET_SENTINEL', str(result))


if __name__ == '__main__':
    unittest.main()
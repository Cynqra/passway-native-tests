import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'verify_android_api.py'


class AndroidApiVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        spec = importlib.util.spec_from_file_location('verify_android_api', SCRIPT)
        self.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.helper)
        self.env = {'PASSWAY_EXPECTED_ANDROID_API': '34', 'PASSWAY_RESULTS': str(self.root)}

    def test_actual_api_is_verified_and_saved(self):
        calls = []
        def run(*args, **kwargs):
            calls.append((args, kwargs))
            return types.SimpleNamespace(returncode=0, stdout='34\r\n')
        self.assertEqual(self.helper.verify(self.env, run), '34')
        self.assertEqual((self.root/'android-api.txt').read_text(), '34\n')
        self.assertEqual(calls[0][0][0], ['adb', 'shell', 'getprop', 'ro.build.version.sdk'])
        self.assertEqual(calls[0][1]['timeout'], 15)

    def test_wrong_api_is_recorded_but_rejected(self):
        with self.assertRaises(RuntimeError):
            self.helper.verify(self.env, lambda *a, **k: types.SimpleNamespace(
                returncode=0, stdout='36\n'))
        self.assertEqual((self.root/'android-api.txt').read_text(), '36\n')

    def test_unknown_selected_api_does_not_call_adb(self):
        for selected in ('', '33', '34;echo bad', '36\nbad'):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                self.helper.verify({**self.env, 'PASSWAY_EXPECTED_ANDROID_API': selected},
                                   lambda *a, **k: self.fail('Unexpected ADB request'))

    def test_failed_adb_or_invalid_output_never_pass(self):
        for code, value in [(1, '34'), (0, ''), (0, '34\n36'), (0, 'not-a-sdk')]:
            with self.subTest(code=code, value=value), self.assertRaises(RuntimeError):
                self.helper.verify(self.env, lambda *a, **k: types.SimpleNamespace(
                    returncode=code, stdout=value))

    def test_single_action_command_works_in_real_subshell_without_shared_variables(self):
        adb = self.root/'adb'
        adb.write_text('#!/bin/sh\nprintf "34\\r\\n"\n')
        adb.chmod(0o700)
        env = {**os.environ, **self.env, 'PATH': str(self.root) + os.pathsep + os.environ['PATH']}
        result = subprocess.run(
            ['/bin/sh', '-c', f'"{sys.executable}" "{SCRIPT}"'],
            env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root/'android-api.txt').read_text(), '34\n')


if __name__ == '__main__':
    unittest.main()
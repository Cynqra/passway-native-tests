"""One emulator-action command: never rely on shell variables across lines."""
import os
from pathlib import Path
import re
import subprocess
import sys


def verify(env, execute=subprocess.run):
    expected = env.get('PASSWAY_EXPECTED_ANDROID_API')
    if expected not in ('34', '35', '36'):
        raise ValueError('Explicit supported Android API selection required')
    result = execute(
        ['adb', 'shell', 'getprop', 'ro.build.version.sdk'],
        capture_output=True, text=True, timeout=15)
    actual = result.stdout.strip()
    if result.returncode or not re.fullmatch(r'\d{2,3}', actual):
        raise RuntimeError('Booted Android API could not be read')
    root = Path(env['PASSWAY_RESULTS'])
    root.mkdir(parents=True, exist_ok=True)
    (root/'android-api.txt').write_text(actual + '\n')
    if actual != expected:
        raise RuntimeError('Booted Android API does not match selected test API')
    return actual


if __name__ == '__main__':
    try:
        print('Booted Android API verified: ' + verify(os.environ))
    except Exception as error:
        print('Android API precondition failed: ' + type(error).__name__, file=sys.stderr)
        sys.exit(1)
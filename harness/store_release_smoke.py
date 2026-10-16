"""Offline UI checks of the actual Play-signed APK, not a Store installation."""
import hashlib
import json
import pathlib
import re
import time

PACKAGE = 'com.passway.app'
VERSION = 8
DIGEST = '6bcc69919bed10d4e1178ff96abd9eda52cdc84a9f708bee8637567b92f4e63c'


class StartupEnvironmentBlocked(RuntimeError):
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic
        super().__init__('Environment blocked: ' + ', '.join(diagnostic['signals']))


def classify_startup_blocker(visible_text, process_log):
    # A historical warning or generic app error alone is not an environment
    # diagnosis. Require the observed Google Play error screen plus evidence.
    if 'check that google play is enabled' not in visible_text.lower():
        return None
    signals = []
    if 'local install check failed due to wrong installer' in process_log.lower():
        signals.append('wrong-installer')
    older = re.search(
        r'Google Play services out of date[^\r\n]*'
        r'Requires\s+(\d+)\s+but found\s+(\d+)', process_log, re.I)
    if older and int(older[1]) > int(older[2]):
        signals.append('play-services-outdated')
    if ('com.pairip.licensecheck.LicenseCheckException' in process_log
            and 'Licensing service could not process request' in process_log):
        signals.append('licensing-service-denied')
    if not signals:
        return None
    # Never persist arbitrary raw log content, credentials, or account data here.
    return {
        'kind': 'environment-blocked', 'signals': signals, 'passed': False,
        'storeInstallationOrAttestationVerified': False,
        'requiredEnvironment': 'Supported Play environment with genuine installation',
        'securityBypassAttempted': False,
    }


def wait_for_release_onboarding(read_tree, locate, read_process_log, seconds=60,
                                clock=time.monotonic, sleep_fn=time.sleep):
    end = clock() + seconds
    while clock() < end:
        tree = read_tree()
        control = locate('welcome-next', tree)
        if control is not None and control.get('visible-to-user') == 'true':
            return control
        text = ' '.join(n.get('text', '') for n in tree.iter('node'))
        if 'check that google play is enabled' in text.lower():
            diagnostic = classify_startup_blocker(text, read_process_log())
            if diagnostic:
                raise StartupEnvironmentBlocked(diagnostic)
        remaining = end - clock()
        if remaining <= 0:
            break
        sleep_fn(min(1, remaining))
    raise TimeoutError('Actual Play release did not reach onboarding within its deadline')


def verify_download(directory, expected_digest=DIGEST):
    directory = pathlib.Path(directory)
    metadata = json.loads((directory / 'download-verification.json').read_text())
    apk = directory / 'passway-store-signed.apk'
    if (metadata.get('package') != PACKAGE
        or type(metadata.get('versionCode')) is not int
        or metadata['versionCode'] != VERSION
        or metadata.get('sha256') != expected_digest
        or hashlib.sha256(apk.read_bytes()).hexdigest() != expected_digest
        or metadata.get('bytes') != apk.stat().st_size):
        raise ValueError('Actual Play release artifact binding failed')
    return metadata


def main():
    # Importing test helpers must never start a phone interaction.
    from driver import ROOT, adb, shell, dump, find, tap, fill, waitfor, shot, record, deadline
    verify_download('store-apk-results')
    (ROOT / 'store-release-complete.json').unlink(missing_ok=True)
    (ROOT / 'startup-environment-blocker.json').unlink(missing_ok=True)
    passed = False
    environment_blocker = None

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        record(name, 'PASS')

    def capture(label):
        shot(label)
        return dump(label)

    try:
        shell('svc', 'wifi', 'disable')
        shell('svc', 'data', 'disable')
        until = time.monotonic() + 25
        while True:
            network = shell('dumpsys', 'connectivity')
            if re.search(r'Active default network:\s*(?:none|null|-1)', network, re.I):
                break
            if time.monotonic() > until:
                raise AssertionError('Offline transport precondition failed')
            time.sleep(.5)
        (ROOT / 'offline-connectivity.txt').write_text(network)
        check('Actual signed release tested without an active default network', True)

        for scale in ('1.0', '1.3', '2.0'):
            label = 'font-' + scale.replace('.', '-')
            shell('am', 'force-stop', PACKAGE)
            shell('pm', 'clear', PACKAGE)
            shell('settings', 'put', 'system', 'font_scale', scale)
            observed = float(shell('settings', 'get', 'system', 'font_scale').strip())
            check(label + ' system font scale applied', observed == float(scale))
            shell('am', 'start', '-W', '-n', PACKAGE + '/.MainActivity')
            def current_process_log():
                pid = shell('pidof', PACKAGE).strip()
                # Constrain logs to the exact currently running app process.
                return adb('logcat', '-d', '--pid=' + pid) if pid.isdigit() else ''
            with deadline(60):
                wait_for_release_onboarding(dump, find, current_process_log)
            capture(label + '-welcome-1')
            check(label + ' release cold start reaches onboarding', True)
            for page in range(2, 5):
                tap('welcome-next')
                waitfor(f'0{page} / 04', 25)
                capture(label + '-welcome-' + str(page))
            check(label + ' all four onboarding pages remain navigable', True)
            tap('get-started')
            waitfor('phone-input', 30)
            capture(label + '-phone')
            fill('phone-input', '111')  # Deliberately invalid; never a real phone.
            tree = dump()
            if any(w.get('type') == '2' for w in tree.iter('window')):
                shell('input', 'keyevent', 'KEYCODE_BACK')
            tap('send-code')
            tree = capture(label + '-invalid-phone')
            text = ' '.join(n.get('text', '') for n in tree.iter('node'))
            check(label + ' invalid phone remains locally rejected',
                  '10 digit' in text and find('verify-input', tree) is None)
            check(label + ' release process remains alive',
                  bool(shell('pidof', PACKAGE).strip()))
        passed = True
        (ROOT / 'store-release-complete.json').write_text(json.dumps({
            'passed': True, 'package': PACKAGE, 'versionCode': VERSION,
            'apkSha256': DIGEST, 'fontScales': [1.0, 1.3, 2.0],
            'scope': 'Actual unmodified Play-signed APK installed by ADB on an offline emulator',
            'storeInstallationVerified': False, 'positiveAttestationVerified': False,
            'authenticatedTwoUserFlowTested': False, 'realSmsSent': False,
        }, indent=2) + '\n')
    except Exception as error:
        if isinstance(error, StartupEnvironmentBlocked):
            environment_blocker = error.diagnostic
            (ROOT / 'startup-environment-blocker.json').write_text(
                json.dumps(environment_blocker, indent=2) + '\n')
        record('Actual signed-release offline UI acceptance', 'FAIL', type(error).__name__)
        try:
            capture('release-failure')
        except Exception:
            pass
        raise
    finally:
        (ROOT / 'store-release-outcome.json').write_text(json.dumps({
            'passed': passed, 'realSmsSent': False,
            'storeInstallationOrAttestationClaimed': False,
            'environmentBlocker': environment_blocker,
        }, indent=2) + '\n')
        try:
            pid = shell('pidof', PACKAGE).strip()
            if pid:
                (ROOT / 'release-process-logcat.txt').write_text(
                    adb('logcat', '-d', '--pid=' + pid))
            shell('settings', 'put', 'system', 'font_scale', '1.0')
        except Exception:
            pass


if __name__ == '__main__':
    main()
"""Offline UI checks of the actual Play-signed APK, not a Store installation."""
import hashlib
import json
import pathlib
import os
import re
import time

PACKAGE = 'com.passway.app'


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



def validate_store_inputs(run_id, version, digest):
    if (not isinstance(run_id, str) or not re.fullmatch(r"[1-9][0-9]{0,19}", run_id)
        or not isinstance(version, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", version)
        or int(version) > 2100000000
        or not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest)):
        raise ValueError("Explicit numeric download run, version and exact SHA256 required")
    return run_id, int(version), digest


def verify_download_run(run, current_sha):
    if (not isinstance(run, dict) or not isinstance(current_sha, str)
        or not re.fullmatch(r"[a-f0-9]{40}", current_sha)
        or run.get('status') != 'completed' or run.get('conclusion') != 'success'
        or run.get('event') != 'workflow_dispatch' or run.get('head_sha') != current_sha
        or run.get('head_branch') != 'validation/isolated-current-native'
        or run.get('path') != '.github/workflows/passway-fresh-native-smoke.yml'
        or run.get('head_repository', {}).get('full_name') != 'Cynqra/passway-native-tests'):
        raise ValueError("Play download must match trusted completed workflow and current revision")


def verify_download(directory, expected_digest, expected_version):
    directory = pathlib.Path(directory)
    metadata_path = directory / "download-verification.json"
    apk_path = directory / "passway-store-signed.apk"

    if not isinstance(expected_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
        raise ValueError("expected_digest must be a lowercase SHA256 hex string")
    if type(expected_version) is not int or not (1 <= expected_version <= 2100000000):
        raise ValueError("expected_version must be a real int in 1..2100000000")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("failed to read metadata") from exc

    if not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")
    if metadata.get("package") != "com.passway.app":
        raise ValueError("metadata package mismatch")

    meta_version = metadata.get("versionCode")
    if type(meta_version) is not int or meta_version != expected_version:
        raise ValueError("metadata versionCode mismatch")

    meta_digest = metadata.get("sha256")
    if not isinstance(meta_digest, str) or meta_digest != expected_digest:
        raise ValueError("metadata sha256 mismatch")

    meta_size = metadata.get("bytes")
    if type(meta_size) is not int or meta_size <= 0:
        raise ValueError("metadata bytes must be a positive real int")

    actual_size = apk_path.stat().st_size
    if not 0 < actual_size <= 150 * 1024 * 1024:
        raise ValueError("APK size outside accepted bound")
    actual_digest = hashlib.sha256(apk_path.read_bytes()).hexdigest()
    if actual_digest != expected_digest:
        raise ValueError("APK sha256 mismatch")

    if meta_size != actual_size:
        raise ValueError("metadata bytes does not match actual APK size")

    return metadata

def main():
    # Importing test helpers must never start a phone interaction.
    from driver import ROOT, adb, shell, dump, find, tap, fill, waitfor, shot, record, deadline
    _, expected_version, expected_digest = validate_store_inputs(
        os.environ.get('PASSWAY_STORE_DOWNLOAD_RUN_ID', ''),
        os.environ.get('PASSWAY_STORE_VERSION_CODE', ''),
        os.environ.get('PASSWAY_STORE_APK_SHA256', ''))
    verify_download('store-apk-results', expected_digest, expected_version)
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
            'passed': True, 'package': PACKAGE, 'versionCode': expected_version,
            'apkSha256': expected_digest, 'fontScales': [1.0, 1.3, 2.0],
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
"""Publish an already verified bundle to INTERNAL TESTING ONLY; never production."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from play_api_access import SafeError, NoRedirect, access_token, safe_http_error, PUBLISHER

REPO = 'Cynqra/passway-native-tests'
BRANCH = 'validation/isolated-current-native'
FINGERPRINT = '98:15:DF:C7:D9:03:55:59:F2:18:9C:B0:0C:06:1D:F7:22:B8:DB:E8:8B:09:2F:62:79:DE:78:2A:3F:FE:3A:CC'

def trusted_run(run, sha, workflow):
    if (run.get('status') != 'completed' or run.get('conclusion') != 'success'
        or run.get('event') != 'workflow_dispatch' or run.get('head_sha') != sha
        or run.get('head_branch') != BRANCH or run.get('path') != '.github/workflows/' + workflow
        or run.get('head_repository', {}).get('full_name') != REPO):
        raise SafeError('Candidate validation run does not match trusted workflow/source')

def verify_artifacts(signed, native, provenance):
    meta = json.loads((signed / 'release-metadata.json').read_text())
    for directory in (signed, native):
        observed = json.loads((directory / 'source-provenance.json').read_text())
        if any(observed.get(k) != provenance.get(k) for k in ('sourceRepository', 'sourceCommit', 'archiveSha256')):
            raise SafeError('Candidate source provenance mismatch')
    if (meta.get('package') != 'com.passway.app' or type(meta.get('versionCode')) is not int
        or not 1 <= meta['versionCode'] <= 2100000000
        or not re.fullmatch(r'\d+\.\d+\.\d+', meta.get('versionName', ''))
        or meta.get('sourceCommit') != provenance['sourceCommit']
        or meta.get('sourceArchiveSha256') != provenance['archiveSha256']):
        raise SafeError('Invalid candidate metadata')
    results = json.loads((native / 'results.json').read_text())
    if len(results) < 75 or any(row.get('status') != 'PASS' for row in results):
        raise SafeError('Native extended assertions incomplete')
    if (json.loads((native / 'complete.json').read_text()).get('status') != 'passed'
        or not json.loads((native / 'extended-complete.json').read_text()).get('passed')
        or not json.loads((native / 'coordinator-result.json').read_text()).get('passed')):
        raise SafeError('Native completion markers missing')
    bundle = signed / 'passway-release.aab'
    if not 0 < bundle.stat().st_size <= 150 * 1024 * 1024:
        raise SafeError('Invalid bundle size')
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    if (signed / 'artifact.sha256').read_text().split()[0] != digest:
        raise SafeError('Signed artifact hash mismatch')
    root = ET.parse(signed / 'AndroidManifest.xml').getroot()
    android = '{http://schemas.android.com/apk/res/android}'
    app = root.find('application')
    if (root.attrib.get('package') != 'com.passway.app'
        or root.attrib.get(android + 'versionCode') != str(meta['versionCode'])
        or root.attrib.get(android + 'versionName') != meta['versionName']
        or app is None or app.attrib.get(android + 'allowBackup') != 'false'
        or app.attrib.get(android + 'debuggable', 'false') != 'false'
        or app.attrib.get(android + 'usesCleartextTraffic', 'false') != 'false'
        or 'FirebaseAppCheckRegistrar' not in (signed / 'AndroidManifest.xml').read_text()):
        raise SafeError('Compiled candidate security metadata mismatch')
    verified = subprocess.run(['jarsigner', '-verify', str(bundle)], capture_output=True, timeout=60)
    cert = subprocess.run(['keytool', '-printcert', '-jarfile', str(bundle)], capture_output=True, text=True, timeout=30)
    if verified.returncode or cert.returncode or FINGERPRINT not in cert.stdout:
        raise SafeError('Actual bundle signature or signer mismatch')
    return meta, bundle.read_bytes(), digest

def send(url, method='GET', headers=None, body=None, binary=None):
    data = binary if binary is not None else json.dumps(body).encode() if body is not None else None
    hdr = dict(headers or {})
    if data is not None:
        hdr['Content-Type'] = 'application/octet-stream' if binary is not None else 'application/json'
    request = urllib.request.Request(url, data=data, headers=hdr, method=method)
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=180) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise SafeError('Oversized Play response')
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raise safe_http_error(url, error.code, error.read(65536)) from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise SafeError('Play release transport or JSON validation failed') from None

def publish_internal(token, meta, bundle, digest, request=send):
    if (meta.get('package') != 'com.passway.app' or type(meta.get('versionCode')) is not int
        or meta['versionCode'] < 1 or hashlib.sha256(bundle).hexdigest() != digest):
        raise SafeError('Invalid internal candidate before network')
    headers = {'Authorization': 'Bearer ' + token}
    edit = request(PUBLISHER, method='POST', headers=headers, body={}).get('id')
    if not isinstance(edit, str) or not edit.isdigit():
        raise SafeError('Invalid Play edit identifier')
    committed = False
    try:
        tracks = request(PUBLISHER + '/' + edit + '/tracks', headers=headers)
        codes = [int(code) for track in tracks.get('tracks', []) for release in track.get('releases', []) for code in release.get('versionCodes', [])]
        if not codes or meta['versionCode'] <= max(codes):
            raise SafeError('Candidate version must exceed every currently released version')
        upload_url = PUBLISHER.replace('/androidpublisher/v3/', '/upload/androidpublisher/v3/') + '/' + edit + '/bundles?uploadType=media'
        uploaded = request(upload_url, method='POST', headers=headers, binary=bundle)
        if uploaded.get('versionCode') != meta['versionCode'] or uploaded.get('sha256', '').lower() != digest:
            raise SafeError('Play upload version/hash verification failed')
        release = {'track': 'internal', 'releases': [{'name': meta['versionName'] + ' (' + str(meta['versionCode']) + ') — candidate validation', 'versionCodes': [str(meta['versionCode'])], 'status': 'completed'}]}
        request(PUBLISHER + '/' + edit + '/tracks/internal', method='PUT', headers=headers, body=release)
        request(PUBLISHER + '/' + edit + ':validate', method='POST', headers=headers, body={})
        request(PUBLISHER + '/' + edit + ':commit', method='POST', headers=headers, body={})
        committed = True
        return {'package': meta['package'], 'versionCode': meta['versionCode'], 'sha256': digest, 'track': 'internal', 'editCommitted': True, 'publicProductionRollout': False, 'storeInstallationOrPositiveAttestationVerified': False}
    finally:
        if not committed:
            request(PUBLISHER + '/' + edit, method='DELETE', headers=headers)

def gh_api(endpoint):
    result = subprocess.run(['gh', 'api', endpoint], capture_output=True, text=True, timeout=40)
    if result.returncode:
        raise SafeError('GitHub release-evidence lookup failed')
    return json.loads(result.stdout)

def main():
    try:
        sha = os.environ['GITHUB_SHA']
        for variable in ('PASSWAY_SIGNED_RUN_ID', 'PASSWAY_NATIVE_RUN_ID'):
            if not re.fullmatch(r'[0-9]{1,20}', os.environ.get(variable, '')):
                raise SafeError('Numeric completed validation run IDs required')
            run = gh_api('repos/' + REPO + '/actions/runs/' + os.environ[variable])
            trusted_run(run, sha, 'passway-fresh-native-smoke.yml')
        for workflow in ('passway-architecture-validation.yml', 'passway-static-security.yml'):
            candidates = gh_api('repos/' + REPO + '/actions/workflows/' + workflow + '/runs?head_sha=' + sha + '&event=workflow_dispatch&status=success&per_page=20').get('workflow_runs', [])
            if not candidates:
                raise SafeError('Same-revision regression, security or static acceptance incomplete')
            trusted_run(candidates[0], sha, workflow)
        for variable, artifact, directory in [('PASSWAY_SIGNED_RUN_ID', 'passway-signed-candidate', 'candidate-signed'), ('PASSWAY_NATIVE_RUN_ID', 'isolated-current-native-evidence', 'candidate-native')]:
            result = subprocess.run(['gh', 'run', 'download', os.environ[variable], '-R', REPO, '-n', artifact, '-D', directory], capture_output=True, timeout=120)
            if result.returncode:
                raise SafeError('Required immutable validation artifact unavailable')
        provenance = json.loads(Path('validation/architecture-provenance.json').read_text())
        if hashlib.sha256(Path('validation/architecture-source.tar.gz').read_bytes()).hexdigest() != provenance['archiveSha256']:
            raise SafeError('Checked-out source archive integrity mismatch')
        meta, bundle, digest = verify_artifacts(Path('candidate-signed'), Path('candidate-native'), provenance)
        result = publish_internal(access_token(os.environ), meta, bundle, digest)
        Path('internal-release-result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
        return 0
    except Exception as error:
        result = {'status': 'FAILED', 'error': str(error) if isinstance(error, SafeError) else type(error).__name__, 'publicProductionRollout': False, 'positiveAttestationVerified': False}
        Path('internal-release-result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())

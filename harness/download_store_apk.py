"""Read-only Google Play-generated APK download, never upload or release edits."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import os
import urllib.parse
import urllib.request
from play_api_access import access_token, request, SafeError, NoRedirect

CERT = '5F97B4BFE27BDBF3AADE7FD1E2E7B323CFDDE1CD8D7FEAA536EA1DB31EF963F2'
BASE = 'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/com.passway.app/generatedApks/'

def selection(response):
    keys = [x for x in response.get('generatedApks', []) if x.get('certificateSha256Hash', '').replace(':', '').upper() == CERT]
    if len(keys) != 1:
        raise SafeError('Expected registered Google Play app-signing certificate unavailable')
    download = keys[0].get('generatedUniversalApk', {}).get('downloadId')
    if not isinstance(download, str) or not 1 <= len(download) <= 4096 or any(ord(c) < 32 for c in download):
        raise SafeError('Google Play universal APK not ready; no arbitrary split/variant selected')
    return download

def verify_badging(text, version_code):
    if type(version_code) is not int or not 1 <= version_code <= 2100000000:
        raise SafeError('Invalid expected APK version')
    match = re.search(r"^package: name='([^']+)' versionCode='([^']+)'", text, re.MULTILINE)
    if not match or match.group(1) != 'com.passway.app' or match.group(2) != str(version_code):
        raise SafeError('Actual APK package/version does not match authenticated download metadata')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version-code', required=True)
    args = parser.parse_args()
    output = Path('store-apk-results');output.mkdir(exist_ok=True)
    try:
        if not re.fullmatch(r'[1-9][0-9]{0,9}', args.version_code) or int(args.version_code) > 2100000000:
            raise SafeError('Invalid store version code')
        token = access_token(os.environ)
        headers = {'Authorization': 'Bearer ' + token}
        listing = request(BASE + args.version_code, headers=headers)
        download = selection(listing)
        url = BASE + args.version_code + '/downloads/' + urllib.parse.quote(download, safe='') + ':download?alt=media'
        target = output / 'passway-store-signed.apk'
        h = hashlib.sha256();size = 0
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.build_opener(NoRedirect).open(req, timeout=120) as response, target.open('wb') as out:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > 150 * 1024 * 1024:
                    raise SafeError('Store APK exceeded size bound')
                out.write(chunk);h.update(chunk)
        if size < 4 or target.read_bytes()[:2] != b'PK':
            raise SafeError('Store response is not an APK archive')
        report = {'package':'com.passway.app','versionCode':int(args.version_code),'sha256':h.hexdigest(),'bytes':size,'expectedPlaySigningCertificateSha256':CERT,'source':'Authenticated Google Play generatedApks API','mutationsAttempted':False,'storeInstallationOrAttestationClaimed':False}
        (output / 'download-verification.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report));return 0
    except Exception as error:
        (output / 'passway-store-signed.apk').unlink(missing_ok=True)
        report = {'status':'FAILED','error':str(error) if isinstance(error,SafeError) else type(error).__name__,'mutationsAttempted':False}
        (output / 'download-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 1

if __name__ == '__main__':
    raise SystemExit(main())

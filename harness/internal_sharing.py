"""Deliver ONE immutable accepted bundle via internal sharing; never edit tracks.
The installation link is encrypted to the operator's public key before artifact
upload. This is canary distribution, not device/attestation acceptance.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
from internal_release import trusted_run, verify_artifacts, gh_api, send, REPO
from play_api_access import SafeError, access_token

APPROVED_HARNESS = '62e9723ae23dd6112965ecfb218210657e0a04c9'
SOURCE = 'ec65e826e456f406a9087da843c4d4d6425d886d'
ARCHIVE = 'b6b17bd4f65dec104f2c7287e297722884695b4351e639ea99642a1b5b563daf'
BUNDLE = '872fb7529f38dff18e5533c1e273d3e51899e73670df1b98873133f813465a9a'
UPLOAD = 'https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/internalappsharing/com.passway.app/artifacts/bundle?uploadType=media'
ACCEPTED_RUNS = ((38941016522, 'passway-fresh-native-smoke.yml'),
                 (38941013183, 'passway-fresh-native-smoke.yml'),
                 (38941001227, 'passway-architecture-validation.yml'),
                 (38941005486, 'passway-static-security.yml'))


def approved_provenance(provenance):
    if any(provenance.get(k) != v for k, v in {
        'sourceRepository': 'naveenbharti310/Paasway', 'sourceCommit': SOURCE,
        'archiveSha256': ARCHIVE}.items()):
        raise SafeError('Internal sharing is restricted to the recorded immutable candidate')


def upload_shared(token, meta, bundle, digest, request=send):
    if (meta.get('package') != 'com.passway.app' or meta.get('versionCode') != 10
        or type(meta.get('versionCode')) is not int or meta.get('versionName') != '0.3.4'
        or meta.get('sourceCommit') != SOURCE or meta.get('sourceArchiveSha256') != ARCHIVE
        or digest != BUNDLE or hashlib.sha256(bundle).hexdigest() != digest):
        raise SafeError('Unapproved candidate denied before upload')
    value = request(UPLOAD, method='POST', headers={'Authorization': 'Bearer ' + token}, binary=bundle)
    link = value.get('downloadUrl', '')
    try:
        url = urlsplit(link)
        valid = (url.scheme == 'https' and url.hostname == 'play.google.com'
                 and not url.username and not url.password and url.port is None
                 and not url.query and not url.fragment
                 and url.path.startswith(('/apps/test/', '/apps/internaltest/')))
    except (ValueError, TypeError):
        valid = False
    fingerprint = value.get('certificateFingerprint', '').replace(':', '').lower()
    if (not valid or value.get('sha256', '').lower() != digest
        or not re.fullmatch(r'[a-f0-9]{64}', fingerprint)):
        raise SafeError('Internal-sharing response identity/link/hash validation failed')
    return {'downloadUrl': link, 'certificateFingerprint': fingerprint,
            'sha256': digest, 'sourceCommit': SOURCE, 'versionCode': 10,
            'package': 'com.passway.app', 'scope': 'Private opt-in canary only; not a track release or attestation proof'}


def encrypt_delivery(value, public_key):
    # Input and output travel through pipes, never command arguments/logs.
    script = r'''
const fs=require('fs'),c=require('crypto');
const publicKey=fs.readFileSync(process.argv[1]);const plain=fs.readFileSync(0);
const key=c.randomBytes(32),iv=c.randomBytes(12),aad=Buffer.from('passway-private-canary-v1');
const cipher=c.createCipheriv('aes-256-gcm',key,iv);cipher.setAAD(aad);
const encrypted=Buffer.concat([cipher.update(plain),cipher.final()]);
const wrapped=c.publicEncrypt({key:publicKey,padding:c.constants.RSA_PKCS1_OAEP_PADDING,oaepHash:'sha256'},key);
console.log(JSON.stringify({format:'passway-private-canary-v1',recipientSha256:c.createHash('sha256').update(publicKey).digest('hex'),key:wrapped.toString('base64'),iv:iv.toString('base64'),tag:cipher.getAuthTag().toString('base64'),ciphertext:encrypted.toString('base64')}));
'''
    result = subprocess.run(['node', '-e', script, str(public_key)],
                            input=json.dumps(value), capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise SafeError('Canary delivery encryption failed; installation link not published')
    return json.loads(result.stdout)


def main():
    try:
        provenance = json.loads(Path('validation/architecture-provenance.json').read_text())
        approved_provenance(provenance)
        if hashlib.sha256(Path('validation/architecture-source.tar.gz').read_bytes()).hexdigest() != ARCHIVE:
            raise SafeError('Source archive changed')
        # Explicit immutable handoff: old accepted SOURCE/BUNDLE, not acceptance
        # of this new distribution workflow or any changed app implementation.
        for run_id, workflow in ACCEPTED_RUNS:
            trusted_run(gh_api(f'repos/{REPO}/actions/runs/{run_id}'), APPROVED_HARNESS, workflow)
        for run_id, name, directory in ((38941016522, 'passway-signed-candidate', 'sharing-signed'),
                                       (38941013183, 'isolated-current-native-evidence', 'sharing-native')):
            result = subprocess.run(['gh', 'run', 'download', str(run_id), '-R', REPO, '-n', name, '-D', directory], capture_output=True, timeout=150)
            if result.returncode:
                raise SafeError('Accepted immutable artifact unavailable')
        meta, bundle, digest = verify_artifacts(Path('sharing-signed'), Path('sharing-native'), provenance)
        if digest != BUNDLE:
            raise SafeError('Accepted bundle digest mismatch')
        payload = upload_shared(access_token(os.environ), meta, bundle, digest)
        encrypted = encrypt_delivery(payload, Path('harness/internal-sharing-recipient.pub'))
        Path('internal-sharing-delivery.encrypted.json').write_text(json.dumps(encrypted, indent=2) + '\n')
        report = {k: v for k, v in payload.items() if k != 'downloadUrl'}
        report.update(status='uploaded', installLinkEncrypted=True, releaseTracksChanged=False,
                      publicProductionRollout=False, positiveStoreAttestationVerified=False,
                      acceptedValidationHarness=APPROVED_HARNESS, distributionHarness=os.environ['GITHUB_SHA'])
        Path('internal-sharing-result.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
        return 0
    except Exception as error:
        report = {'status': 'FAILED', 'error': str(error) if isinstance(error, SafeError) else type(error).__name__,
                  'releaseTracksChanged': False, 'positiveStoreAttestationVerified': False}
        Path('internal-sharing-result.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())

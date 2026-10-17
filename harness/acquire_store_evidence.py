"""Retrieve exact trusted read-only Play download evidence, never install or publish."""
import json,os,pathlib,subprocess
from store_release_smoke import validate_store_inputs,verify_download_run,verify_download

def acquire(env, runner=subprocess.run):
    run_id,version,digest=validate_store_inputs(env.get('PASSWAY_STORE_DOWNLOAD_RUN_ID',''),env.get('PASSWAY_STORE_VERSION_CODE',''),env.get('PASSWAY_STORE_APK_SHA256',''))
    sha=env.get('GITHUB_SHA','')
    run=runner(['gh','api','repos/Cynqra/passway-native-tests/actions/runs/'+run_id],capture_output=True,text=True,timeout=40)
    if run.returncode:raise ValueError('Trusted Play download run lookup failed')
    verify_download_run(json.loads(run.stdout),sha)
    result=runner(['gh','run','download',run_id,'-R','Cynqra/passway-native-tests','-n','google-play-signed-physical-device-apk','-D','store-apk-results'],capture_output=True,text=True,timeout=120)
    if result.returncode:raise ValueError('Trusted APK artifact unavailable')
    verify_download('store-apk-results',digest,version)
    return {'downloadRunId':run_id,'versionCode':version,'sha256':digest,'harnessCommit':sha,'scope':'Trusted artifact binding only; actual signature and manifest reverified before any offline installation; not Store attestation'}
if __name__=='__main__':
    out=pathlib.Path('store-ui-results');out.mkdir(exist_ok=True)
    try:
        report=acquire(os.environ);(out/'trusted-download-binding.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    except Exception:
        print('Store artifact binding failed before installation. No credentials or provider bodies retained.');raise SystemExit(1)

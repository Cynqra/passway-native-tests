"""One immutable test attempt. Never wait for or execute live branch patches."""
import json, os, pathlib, subprocess, sys, time
from status import publish, ROOT

def main():
 ROOT.mkdir(exist_ok=True, parents=True)
 # A stale success marker must never turn a later run into a pass.
 (ROOT/'complete.json').unlink(missing_ok=True)
 os.environ['PASSWAY_ATTEMPT']='1'
 started=time.monotonic()
 publish('native_test_started')
 try:
  code=subprocess.run([sys.executable,'harness/native_e2e.py'],timeout=900).returncode
 except subprocess.TimeoutExpired:
  code=124
 complete=ROOT/'complete.json'
 passed=code==0 and complete.is_file()
 details={'exit_code':code,'duration_seconds':round(time.monotonic()-started,2),
          'passed':passed,'scope':'checked-out revision; one attempt; no live patching'}
 (ROOT/'coordinator-result.json').write_text(json.dumps(details,indent=2))
 publish('passed' if passed else 'failed',**details)
 return 0 if passed else (code or 1)

if __name__=='__main__':sys.exit(main())

"""One immutable test attempt. Never wait for or execute live branch patches."""
import json, os, pathlib, subprocess, sys, time
from startup_log_collector import StartupLogCollector
from status import publish, ROOT

def main():
 ROOT.mkdir(exist_ok=True, parents=True)
 # A stale success marker must never turn a later run into a pass.
 (ROOT/'accessibility-complete.json').unlink(missing_ok=True)
 (ROOT/'complete.json').unlink(missing_ok=True)
 (ROOT/'extended-complete.json').unlink(missing_ok=True)
 (ROOT/'startup-phases.jsonl').unlink(missing_ok=True)
 os.environ['PASSWAY_ATTEMPT']='1'
 started=time.monotonic()
 publish('native_test_started')
 with StartupLogCollector(ROOT/'startup-phases.jsonl', started=started) as collector:
  try:
   # Destructive safety journeys reuse the same APK/emulator but add identities
   # and independently audited transitions. Still one immutable bounded attempt.
   budget=1500 if os.environ.get('PASSWAY_NATIVE_EXTENDED')=='1' else 900
   code=subprocess.run([sys.executable,'harness/native_isolated_e2e.py'],timeout=budget).returncode
  except subprocess.TimeoutExpired:
   code=124
 complete=ROOT/'complete.json'
 passed=code==0 and complete.is_file() and (os.environ.get('PASSWAY_NATIVE_ACCESSIBILITY')!='1' or (ROOT/'accessibility-complete.json').is_file()) and (
  os.environ.get('PASSWAY_NATIVE_EXTENDED')!='1' or (ROOT/'extended-complete.json').is_file())
 details={'exit_code':code,'duration_seconds':round(time.monotonic()-started,2),
          'passed':passed,'scope':'current-source isolated emulators; one attempt; no live patching',
          'startup_diagnostics':collector.summary()}
 (ROOT/'coordinator-result.json').write_text(json.dumps(details,indent=2))
 publish('passed' if passed else 'failed',**details)
 return 0 if passed else (code or 1)

if __name__=='__main__':sys.exit(main())

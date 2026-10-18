"""Promote verified version17 to built-in beta only. Never modify production."""
import json,os,re,hashlib,subprocess
from pathlib import Path
from play_api_access import access_token,SafeError,PUBLISHER
from internal_release import send
REPO='Cynqra/passway-native-tests'
SOURCE_HARNESS='babe2cf1a9db161940dd2ea5adb9f90126cda6a6'
SOURCE='87134a3099697edfbbd22f11eb786265523d9afa'
BUNDLE='048655e3e398b321974cedde59054ff7087094103d481f02a410e30eeb03879d'
RUNS=[39140553524,39140555016,39141210928,39141212728,39142281976,39142480247]
def gh(path):
 p=subprocess.run(['gh','api',path],capture_output=True,text=True,timeout=40)
 if p.returncode:raise SafeError('Immutable GitHub evidence lookup failed')
 return json.loads(p.stdout)
def verify_evidence():
 for rid in RUNS:
  r=gh(f'repos/{REPO}/actions/runs/{rid}')
  if (r.get('head_sha')!=SOURCE_HARNESS or r.get('head_branch')!='validation/isolated-current-native' or r.get('event')!='workflow_dispatch' or r.get('status')!='completed' or r.get('conclusion')!='success' or r.get('head_repository',{}).get('full_name')!=REPO):raise SafeError('Required exact-source release evidence is not successful')
 p=json.loads(Path('validation/architecture-provenance.json').read_text())
 if p.get('sourceCommit')!=SOURCE or hashlib.sha256(Path('validation/architecture-source.tar.gz').read_bytes()).hexdigest()!=p.get('archiveSha256'):raise SafeError('Source snapshot changed')
 return True

def release_codes(track):return sorted((r.get('status'),tuple(r.get('versionCodes',[]))) for r in track.get('releases',[]))
def checked_state(tracks,bundles):
 indexed={t.get('track'):t for t in tracks}
 if release_codes(indexed.get('production',{}))!=[('completed',('16',))]:raise SafeError('Production changed; no testing update attempted')
 if not any(r.get('status')=='completed' and r.get('versionCodes')==['17'] for r in indexed.get('internal',{}).get('releases',[])):raise SafeError('Verified internal17 is not current')
 if len([b for b in bundles if b.get('versionCode')==17 and b.get('sha256','').lower()==BUNDLE])!=1:raise SafeError('Registered bundle17 hash mismatch')
 if 'beta' not in indexed:raise SafeError('Built-in open testing track is unavailable')
 existing=indexed['beta'].get('releases',[])
 if existing and release_codes(indexed['beta'])!=[('completed',('17',))]:raise SafeError('Existing testing release will not be overwritten')
 return indexed['production'],bool(existing)

def promote(token,publish=False,request=send):
 headers={'Authorization':'Bearer '+token};edit=None;committed=False
 report={'package':'com.passway.app','versionCode':17,'track':'beta','productionChanged':False,'submitted':False,'publicAvailabilityVerified':False,'knownGate':'Actual ADB/offline Play APK UI test was environment-blocked; genuine Store installation and real-device latency are not certified.'}
 def call(url,**kw):return request(url,headers=headers,**kw)
 try:
  edit=call(PUBLISHER,method='POST',body={}).get('id')
  if not isinstance(edit,str) or not edit.isdigit():raise SafeError('Invalid Play edit')
  tracks=call(PUBLISHER+'/'+edit+'/tracks').get('tracks',[])
  bundles=call(PUBLISHER+'/'+edit+'/bundles').get('bundles',[])
  prod,existing=checked_state(tracks,bundles)
  report['productionBefore']=prod;report['testingBefore']=next(t for t in tracks if t.get('track')=='beta')
  countries=call(PUBLISHER+'/'+edit+'/countryAvailability/beta')
  report['testingCountries']=countries
  report['testingGoogleGroupConfigured']=bool(call(PUBLISHER+'/'+edit+'/testers/beta').get('googleGroups'))
  if not publish:return report
  if report['testingGoogleGroupConfigured']:raise SafeError('Beta has closed group targeting; open enrollment requires Console verification')
  if not countries.get('countries') and not countries.get('restOfWorld'):raise SafeError('Open testing has no countries configured; Console action required')
  if existing:report['alreadyPresent']=True;return report
  body={'track':'beta','releases':[{'name':'0.3.11 (17) public testing','versionCodes':['17'],'status':'completed','releaseNotes':[{'language':'en-US','text':'Improved connection speed and chat updates. Fixed message refresh and recovery issues.'}]}]}
  updated=call(PUBLISHER+'/'+edit+'/tracks/beta',method='PUT',body=body)
  if release_codes(updated)!=[('completed',('17',))]:raise SafeError('Testing update readback mismatch')
  if call(PUBLISHER+'/'+edit+'/tracks/production')!=prod:raise SafeError('Production unexpectedly changed within temporary edit')
  call(PUBLISHER+'/'+edit+':validate',method='POST',body={})
  call(PUBLISHER+'/'+edit+':commit',method='POST',body={});committed=True
  report['submitted']=True;report['reviewApprovalVerified']=False;report['optInUrl']='https://play.google.com/apps/testing/com.passway.app'
  return report
 finally:
  if edit and not committed:call(PUBLISHER+'/'+edit,method='DELETE')

def main():
 result={}
 try:
  action=os.environ.get('PASSWAY_OPEN_TESTING_ACTION')
  if action not in ['inspect','submit']:raise SafeError('Explicit inspect or submit action required')
  verify_evidence();result=promote(access_token(os.environ),publish=action=='submit');result['evidenceVerified']=True;returncode=0
 except Exception as e:
  result={'status':'BLOCKED','error':str(e) if isinstance(e,SafeError) else type(e).__name__,'submitted':None,'submissionOutcome':'Unconfirmed. Inspect Play before retrying any mutation.','productionChanged':False};returncode=1
 Path('open-testing17-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return returncode
if __name__=='__main__':raise SystemExit(main())

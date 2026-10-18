"""Submit only the exact validated version18 production update for normal Google review."""
import hashlib,json,os
from pathlib import Path
from play_api_access import access_token,SafeError,PUBLISHER
from internal_release import send
from open_testing17 import gh,release_codes
REPO='Cynqra/passway-native-tests'
HARNESS='6a7fcd2e76316ec0ae24ffaa4581d716918e8967'
SOURCE='1fe24483a8430137ae94e234ee43ba8c1655b855'
BUNDLE='0ff4ffaf97b46cf5cf0fbd364baab1fd3e3b6860cee262e9b33e2cca95b69d05'
RUNS=[39150504966,39150502989,39150506913,39150508741,39152796864]
def verify_evidence():
 for rid in RUNS:
  r=gh(f'repos/{REPO}/actions/runs/{rid}')
  if (r.get('head_sha')!=HARNESS or r.get('head_branch')!='validation/isolated-current-native' or r.get('event')!='workflow_dispatch' or r.get('status')!='completed' or r.get('conclusion')!='success' or r.get('head_repository',{}).get('full_name')!=REPO):raise SafeError('Exact-source version18 evidence is not successful')
 p=json.loads(Path('validation/architecture-provenance.json').read_text())
 if p.get('sourceCommit')!=SOURCE or hashlib.sha256(Path('validation/architecture-source.tar.gz').read_bytes()).hexdigest()!=p.get('archiveSha256'):raise SafeError('Candidate source changed')
def submit(token,publish=False,request=send):
 headers={'Authorization':'Bearer '+token};edit=None;committed=False
 report={'versionCode':18,'track':'production','submitted':False,'reviewApprovalVerified':False,'publicAvailabilityVerified':False,'scope':'Normal Google review submission of existing optimized18 only. No listing, country, tester, billing or permission changes. Real SMS and positive Store attestation not certified.'}
 def call(url,**kw):return request(url,headers=headers,**kw)
 try:
  edit=call(PUBLISHER,method='POST',body={}).get('id')
  if not isinstance(edit,str) or not edit.isdigit():raise SafeError('Invalid edit')
  tracks=call(PUBLISHER+'/'+edit+'/tracks').get('tracks',[])
  prod=next((t for t in tracks if t.get('track')=='production'),{})
  internal=next((t for t in tracks if t.get('track')=='internal'),{})
  report['productionBefore']=prod
  if release_codes(prod) not in [[('completed',('16',))],[('completed',('18',))]]:raise SafeError('Unexpected production state; no mutation attempted')
  if release_codes(internal)!=[('completed',('18',))]:raise SafeError('Expected internal18 is not current')
  bundles=call(PUBLISHER+'/'+edit+'/bundles').get('bundles',[])
  if len([b for b in bundles if b.get('versionCode')==18 and b.get('sha256','').lower()==BUNDLE])!=1:raise SafeError('Registered18 bundle hash mismatch')
  report['bundleSha256Verified']=BUNDLE
  if release_codes(prod)==[('completed',('18',))]:report['alreadyPresent']=True;return report
  before={t['track']:t for t in tracks if t.get('track')!='production'}
  if not publish:return report
  body={'track':'production','releases':[{'name':'0.3.12 (18)','versionCodes':['18'],'status':'completed','releaseNotes':[{'language':'en-US','text':'Improved connection and chat responsiveness. Optimized Android release size and code, with improved crash diagnostics.'}]}]}
  updated=call(PUBLISHER+'/'+edit+'/tracks/production',method='PUT',body=body)
  if release_codes(updated)!=[('completed',('18',))]:raise SafeError('Production edit readback mismatch')
  after={t['track']:t for t in call(PUBLISHER+'/'+edit+'/tracks').get('tracks',[]) if t.get('track')!='production'}
  if before!=after:raise SafeError('Unrelated tracks changed within edit')
  call(PUBLISHER+'/'+edit+':validate',method='POST',body={})
  report['commitAttempted']=True
  call(PUBLISHER+'/'+edit+':commit',method='POST',body={});committed=True
  report['submitted']=True;report['productionAfter']=updated
  return report
 finally:
  if edit and not committed:call(PUBLISHER+'/'+edit,method='DELETE')
def main():
 try:
  action=os.environ.get('PASSWAY_PRODUCTION18_ACTION')
  if action not in ['inspect','submit']:raise SafeError('Explicit inspect or submit action required')
  verify_evidence();result=submit(access_token(os.environ),action=='submit');result['evidenceVerified']=True;code=0
 except Exception as e:
  result={'versionCode':18,'status':'BLOCKED','submitted':None,'error':str(e) if isinstance(e,SafeError) else type(e).__name__,'submissionOutcome':'Inspect Play state before any mutation retry.'};code=1
 Path('production18-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return code
if __name__=='__main__':raise SystemExit(main())

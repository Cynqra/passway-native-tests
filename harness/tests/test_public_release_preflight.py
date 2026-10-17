import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
import public_release_preflight as m
from play_api_access import SafeError
class PublicPreflightTests(unittest.TestCase):
 def execute(self,variant=None):
  calls=[]
  def request(url,method='GET',headers=None,body=None,error_observer=None):
   calls.append((url,method,body));self.assertNotIn(':commit',url);self.assertNotIn('/upload/',url)
   if url==m.PUBLISHER:return {'id':'123'}
   if method=='DELETE':return {}
   if url.endswith('/tracks'):return {'tracks':[{'track':'internal','releases':[{'status':'completed','versionCodes':['12' if variant=='changed-internal' else '13']}]},{'track':'production','releases':[{'status':'completed'}] if variant=='existing-production' else []}]}
   if url.endswith('/bundles'):return {'bundles':[{'versionCode':13,'sha256':'wrong' if variant=='wrong-hash' else m.BUNDLE_SHA}]}
   if url.endswith('/details'):return {'defaultLanguage':'en-US','contactEmail':'synthetic@example.invalid'}
   if url.endswith('/listings'):return {'listings':[{'title':'Passway','shortDescription':'Synthetic','fullDescription':'Synthetic'}]}
   if url.endswith('/tracks/production'):
    if variant=='google-draft-block':error_observer(400,json.dumps({'error':{'message':'Only releases with status draft may be created on draft app.'}}).encode());raise SafeError('Play capability check rejected request (HTTP 400)')
    self.assertEqual(body['releases'][0]['versionCodes'],['13']);return {}
   if url.endswith(':validate'):
    if variant=='validation-error':raise SafeError('Synthetic validation failure')
    return {}
   self.fail('Unexpected URL')
  return m.preflight('synthetic-not-a-real-token',request),calls
 def test_validates_exact_existing_candidate_without_commit_or_upload(self):
  r,c=self.execute();self.assertTrue(r['validated']);self.assertTrue(r['temporaryEditDeleted']);self.assertFalse(r['commitAttempted']);self.assertFalse(r['publicProductionRollout']);self.assertFalse(r['uploadAttempted']);self.assertEqual(c[-1][1],'DELETE')
 def test_hash_mismatch_stops_before_any_track_write(self):
  r,c=self.execute('wrong-hash');self.assertFalse(r['validated']);self.assertTrue(r['temporaryEditDeleted']);self.assertFalse(any(x[1]=='PUT' for x in c))
 def test_existing_production_is_not_overwritten(self):
  r,c=self.execute('existing-production');self.assertFalse(r['validated']);self.assertTrue(r['temporaryEditDeleted']);self.assertFalse(any(x[1]=='PUT' for x in c))
 def test_changed_internal_is_not_promoted(self):
  r,c=self.execute('changed-internal');self.assertFalse(r['validated']);self.assertTrue(r['temporaryEditDeleted']);self.assertFalse(any(x[1]=='PUT' for x in c))
 def test_google_draft_restriction_is_reported_not_bypassed(self):
  r,c=self.execute('google-draft-block');self.assertFalse(r['validated']);self.assertEqual(r['googleRequirement']['requirement'],'APP_SETUP_REQUIRED');self.assertTrue(r['temporaryEditDeleted'])
 def test_validation_error_still_cleans_up(self):
  r,c=self.execute('validation-error');self.assertFalse(r['validated']);self.assertEqual(c[-1][1],'DELETE')
 def test_provider_text_and_tokens_are_never_retained(self):
  r=m.reason_from_error(403,json.dumps({'error':{'message':'Permission denied synthetic-secret-user@example.invalid'}}).encode());self.assertEqual(r,{'httpStatus':403,'requirement':'PRODUCTION_PERMISSION_REQUIRED'});self.assertNotIn('synthetic-secret',str(r))
 def test_unknown_provider_message_is_not_guessed(self):
  self.assertEqual(m.reason_from_error(400,b'not-json')['requirement'],'GOOGLE_VALIDATION_REJECTED')

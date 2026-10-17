import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
import public_release_draft as m
from public_release_preflight import BUNDLE_SHA
from play_api_access import SafeError
class PublicDraftTests(unittest.TestCase):
 def execute(self,variant=None,commit=True):
  calls=[]
  def request(url,method='GET',headers=None,body=None,error_observer=None):
   calls.append((url,method,body));self.assertNotIn('/upload/',url)
   if url==m.PUBLISHER:return {'id':'123'}
   if method=='DELETE':return {}
   if url.endswith('/tracks'):return {'tracks':[{'track':'internal','releases':[{'status':'completed','versionCodes':['12' if variant=='internal' else '13']}]},{'track':'production','releases':[{'status':'completed','versionCodes':['12']}] if variant=='production' else []}]}
   if url.endswith('/bundles'):return {'bundles':[{'versionCode':13,'sha256':'wrong' if variant=='hash' else BUNDLE_SHA}]}
   if url.endswith('/details'):return {'defaultLanguage':'bad/locale' if variant=='locale' else 'en-US'}
   if url.endswith('/listings'):return {'listings':[]}
   if '/images/' in url:
    if variant=='official-schema':raise SafeError('Synthetic official schema 404')
    return {'images':[]}
   if any(url.endswith('/listings/en-US/'+kind) for kind in ['icon','featureGraphic','phoneScreenshots']):return {'images':[]}
   if '/listings/en-US' in url and method=='PUT':
    if variant=='listing-error':raise SafeError('Synthetic listing failure')
    return {}
   if url.endswith('/tracks/production'):
    self.assertEqual(body['releases'][0]['status'],'draft');self.assertEqual(body['releases'][0]['versionCodes'],['13']);return {}
   if url.endswith(':validate'):
    if variant=='validation':raise SafeError('Synthetic validation failure')
    return {}
   if ':commit' in url:
    self.assertTrue(url.endswith(':commit?changesNotSentForReview=true'))
    if variant=='commit':raise SafeError('Synthetic ambiguous commit failure')
    return {}
   self.fail('Unexpected operation')
  return m.prepare_draft('synthetic-token',request,commit=commit),calls
 def test_only_exact_verified_draft_and_factual_copy_are_saved(self):
  r,c=self.execute();self.assertTrue(r['draftCommitted']);self.assertTrue(r['listingTextSaved']);self.assertFalse(r['publicProductionRollout']);self.assertFalse(r['reviewSubmitted']);self.assertEqual(sum(':commit' in x[0] for x in c),1);self.assertFalse(any(x[1]=='DELETE' for x in c))
 def test_hash_mismatch_stops_before_listing_or_release_writes(self):
  r,c=self.execute('hash');self.assertFalse(r['draftCommitted']);self.assertTrue(r['temporaryEditDeleted']);self.assertFalse(any(x[1]=='PUT' for x in c))
 def test_existing_public_release_never_overwritten(self):
  r,c=self.execute('production');self.assertFalse(r['draftCommitted']);self.assertFalse(any(x[1]=='PUT' for x in c))
 def test_changed_internal_candidate_never_used(self):
  r,c=self.execute('internal');self.assertFalse(r['draftCommitted']);self.assertFalse(any(x[1]=='PUT' for x in c))
 def test_invalid_locale_never_becomes_url_path(self):
  r,c=self.execute('locale');self.assertFalse(r['draftCommitted']);self.assertTrue(r['temporaryEditDeleted']);self.assertFalse(any(x[1]=='PUT' for x in c))
 def test_listing_failure_cleans_up_without_release_write_or_commit(self):
  r,c=self.execute('listing-error');self.assertFalse(r['draftCommitted']);self.assertTrue(r['temporaryEditDeleted']);self.assertFalse(any('/tracks/production' in x[0] or ':commit' in x[0] for x in c))
 def test_validation_failure_never_commits(self):
  r,c=self.execute('validation');self.assertFalse(r['draftCommitted']);self.assertTrue(r['temporaryEditDeleted']);self.assertFalse(any(':commit' in x[0] for x in c))
 def test_ambiguous_commit_is_not_retried_or_claimed_public(self):
  r,c=self.execute('commit');self.assertFalse(r['draftCommitted']);self.assertFalse(r['publicProductionRollout']);self.assertEqual(sum(':commit' in x[0] for x in c),1)
 def test_store_copy_is_bounded_and_does_not_invent_security_guarantees(self):
  self.assertLessEqual(len(m.SHORT),80);self.assertLessEqual(len(m.FULL),4000);self.assertIn('up to 72 hours',m.FULL);self.assertIn('reported content',m.FULL);self.assertIn('Limerencetechnologies@gmail.com',m.FULL);self.assertNotIn('end to end encrypted',m.FULL.lower());self.assertNotIn('bug free',m.FULL.lower())

 def test_image_inventory_uses_official_discovery_routes(self):
  r,c=self.execute('official-schema');self.assertTrue(r['draftCommitted'])
  observed=[u for u,method,body in c if method=='GET' and any(k in u for k in ['icon','featureGraphic','phoneScreenshots'])]
  self.assertEqual(observed,[m.PUBLISHER+'/123/listings/en-US/'+k for k in ['icon','featureGraphic','phoneScreenshots']])
 def test_google_error_records_exact_operation_without_secrets(self):
  import json
  value=m.sanitized_google_error(403,json.dumps({'error':{'status':'PERMISSION_DENIED','message':'Permission denied for synthetic@example.invalid Bearer synthetic-token'}}).encode(),'validate_draft_edit')
  self.assertEqual(value['operation'],'validate_draft_edit');self.assertEqual(value['status'],'PERMISSION_DENIED');self.assertNotIn('synthetic@example.invalid',str(value));self.assertNotIn('synthetic-token',str(value))
 def test_generic_denial_does_not_infer_a_missing_production_role(self):
  import json
  from public_release_preflight import reason_from_error
  self.assertEqual(reason_from_error(403,json.dumps({'error':{'message':'Permission denied'}}).encode())['requirement'],'AUTHORIZATION_OR_ACCOUNT_RESTRICTION')
 def test_diagnostic_only_mode_never_commits_even_when_validation_passes(self):
  r,c=self.execute(commit=False)
  self.assertTrue(r['validated']);self.assertTrue(r['diagnosticOnly']);self.assertFalse(r['draftCommitted']);self.assertTrue(r['temporaryEditDeleted']);self.assertFalse(any(':commit' in x[0] for x in c))

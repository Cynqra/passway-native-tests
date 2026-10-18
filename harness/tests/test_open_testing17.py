import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import open_testing17 as m
from play_api_access import SafeError
class TestingPromotion(unittest.TestCase):
 def setUp(self):
  self.prod={'track':'production','releases':[{'status':'completed','versionCodes':['16']}]}
  self.internal={'track':'internal','releases':[{'status':'completed','versionCodes':['17']}]};self.beta={'track':'beta','releases':[]}
  self.bundles=[{'versionCode':17,'sha256':m.BUNDLE}];self.countries={'countries':[{'countryCode':'IN'}],'restOfWorld':False};self.groups={};self.calls=[];self.validation_error=False
 def request(self,url,method='GET',headers=None,body=None,**kw):
  self.calls.append((url,method,body));self.assertEqual(headers,{'Authorization':'Bearer synthetic'})
  if url==m.PUBLISHER and method=='POST':return {'id':'123'}
  if method=='DELETE':return {}
  if url.endswith('/tracks'):return {'tracks':[self.prod,self.internal,self.beta]}
  if url.endswith('/bundles'):return {'bundles':self.bundles}
  if url.endswith('/countryAvailability/beta'):return self.countries
  if url.endswith('/testers/beta'):return self.groups
  if url.endswith('/tracks/beta') and method=='PUT':self.beta=body;return body
  if url.endswith('/tracks/production') and method=='GET':return self.prod
  if url.endswith(':validate'):
   if self.validation_error:raise SafeError('Synthetic Google validation failure')
   return {}
  if url.endswith(':commit'):return {}
  raise AssertionError('Unexpected request')
 def tearDown(self):
  self.assertFalse(any('/tracks/production' in u and v!='GET' for u,v,_ in self.calls))
  self.assertFalse(any('/testers/' in u and v!='GET' for u,v,_ in self.calls))
 def committed(self):return any(u.endswith(':commit') for u,_,_ in self.calls)
 def test_inspect_never_commits_or_updates(self):
  r=m.promote('synthetic',False,self.request);self.assertFalse(r['submitted']);self.assertFalse(self.committed());self.assertTrue(any(v=='DELETE' for _,v,_ in self.calls));self.assertFalse(any(v=='PUT' for _,v,_ in self.calls))
 def test_verified_submission_changes_only_beta(self):
  r=m.promote('synthetic',True,self.request);self.assertTrue(r['submitted']);self.assertTrue(self.committed());self.assertFalse(r['publicAvailabilityVerified']);self.assertFalse(r['productionChanged']);self.assertFalse(any(v=='DELETE' for _,v,_ in self.calls))
 def test_hash_mismatch_never_updates(self):
  self.bundles[0]['sha256']='0'*64
  with self.assertRaises(SafeError):m.promote('synthetic',True,self.request)
  self.assertFalse(self.committed());self.assertFalse(any(v=='PUT' for _,v,_ in self.calls))
 def test_production_change_blocks(self):
  self.prod['releases'][0]['versionCodes']=['18']
  with self.assertRaises(SafeError):m.promote('synthetic',True,self.request)
  self.assertFalse(self.committed())
 def test_no_countries_blocks(self):
  self.countries={'countries':[]}
  with self.assertRaises(SafeError):m.promote('synthetic',True,self.request)
  self.assertFalse(self.committed())
 def test_closed_group_blocks_open_testing_claim(self):
  self.groups={'googleGroups':['synthetic@example.invalid']}
  with self.assertRaises(SafeError):m.promote('synthetic',True,self.request)
  self.assertFalse(self.committed())
 def test_existing_different_beta_is_not_overwritten(self):
  self.beta['releases']=[{'status':'completed','versionCodes':['15']}]
  with self.assertRaises(SafeError):m.promote('synthetic',True,self.request)
  self.assertFalse(self.committed())
 def test_existing_same_version_is_idempotent(self):
  self.beta['releases']=[{'status':'completed','versionCodes':['17']}]
  r=m.promote('synthetic',True,self.request);self.assertTrue(r['alreadyPresent']);self.assertFalse(self.committed());self.assertFalse(any(v=='PUT' for _,v,_ in self.calls))
 def test_validation_failure_deletes_edit_without_commit(self):
  self.validation_error=True
  with self.assertRaises(SafeError):m.promote('synthetic',True,self.request)
  self.assertFalse(self.committed());self.assertTrue(any(v=='DELETE' for _,v,_ in self.calls))
if __name__=='__main__':unittest.main()

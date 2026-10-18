import sys,pathlib,unittest,copy
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import production18 as m
from play_api_access import SafeError
class Production18(unittest.TestCase):
 def setUp(self):
  self.prod={'track':'production','releases':[{'status':'completed','versionCodes':['16']}]};self.internal={'track':'internal','releases':[{'status':'completed','versionCodes':['18']}]};self.beta={'track':'beta','releases':[{'status':'completed','versionCodes':['17']}]};self.bundle={'versionCode':18,'sha256':m.BUNDLE};self.calls=[];self.fail_validate=False;self.fail_commit=False;self.change_beta=False
 def request(self,url,method='GET',headers=None,body=None,**kw):
  self.calls.append((url,method,body));self.assertEqual(headers,{'Authorization':'Bearer synthetic'})
  if url==m.PUBLISHER and method=='POST':return {'id':'123'}
  if method=='DELETE':return {}
  if url.endswith('/tracks'):return copy.deepcopy({'tracks':[self.prod,self.internal,self.beta]})
  if url.endswith('/bundles'):return {'bundles':[self.bundle]}
  if url.endswith('/tracks/production') and method=='PUT':
   self.prod=body
   if self.change_beta:self.beta['releases']=[]
   return body
  if url.endswith(':validate'):
   if self.fail_validate:raise SafeError('Validation rejected')
   return {}
  if url.endswith(':commit'):
   if self.fail_commit:raise SafeError('Ambiguous commit')
   return {}
  raise AssertionError(url)
 def committed(self):return any(u.endswith(':commit') for u,_,_ in self.calls)
 def tearDown(self):
  self.assertFalse(any(v=='PUT' and not u.endswith('/tracks/production') for u,v,_ in self.calls))
  self.assertFalse(any('changesNotSentForReview' in u for u,_,_ in self.calls))
 def test_inspection_is_readonly(self):
  r=m.submit('synthetic',False,self.request);self.assertFalse(r['submitted']);self.assertFalse(any(v=='PUT' for _,v,_ in self.calls));self.assertFalse(self.committed())
 def test_submit_exact18_normal_review(self):
  r=m.submit('synthetic',True,self.request);self.assertTrue(r['submitted']);self.assertTrue(self.committed());self.assertFalse(r['reviewApprovalVerified']);self.assertFalse(any(v=='DELETE' for _,v,_ in self.calls))
 def test_hash_mismatch_blocks(self):
  self.bundle['sha256']='0'*64
  with self.assertRaises(SafeError):m.submit('synthetic',True,self.request)
  self.assertFalse(any(v=='PUT' for _,v,_ in self.calls))
 def test_other_production_blocks(self):
  self.prod['releases'][0]['versionCodes']=['19']
  with self.assertRaises(SafeError):m.submit('synthetic',True,self.request)
  self.assertFalse(self.committed())
 def test_old_internal_blocks(self):
  self.internal['releases'][0]['versionCodes']=['17']
  with self.assertRaises(SafeError):m.submit('synthetic',True,self.request)
  self.assertFalse(self.committed())
 def test_already18_no_resubmission(self):
  self.prod['releases'][0]['versionCodes']=['18'];r=m.submit('synthetic',True,self.request);self.assertTrue(r['alreadyPresent']);self.assertFalse(self.committed());self.assertFalse(any(v=='PUT' for _,v,_ in self.calls))
 def test_validation_rejection_no_commit(self):
  self.fail_validate=True
  with self.assertRaises(SafeError):m.submit('synthetic',True,self.request)
  self.assertFalse(self.committed());self.assertTrue(any(v=='DELETE' for _,v,_ in self.calls))
 def test_ambiguous_commit_not_retried(self):
  self.fail_commit=True
  with self.assertRaises(SafeError):m.submit('synthetic',True,self.request)
  self.assertEqual(sum(u.endswith(':commit') for u,_,_ in self.calls),1)
 def test_unrelated_track_change_aborts(self):
  self.change_beta=True
  with self.assertRaises(SafeError):m.submit('synthetic',True,self.request)
  self.assertFalse(self.committed())
if __name__=='__main__':unittest.main()

import hashlib,json,pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
import store_release_smoke as m
class CurrentStoreVersionTests(unittest.TestCase):
 def test_current_authenticated_artifact_is_not_pinned_to_historical_version_eight(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);data=b'PK-current-version-fixture';(p/'passway-store-signed.apk').write_bytes(data);digest=hashlib.sha256(data).hexdigest();metadata={'package':'com.passway.app','versionCode':13,'bytes':len(data),'sha256':digest};(p/'download-verification.json').write_text(json.dumps(metadata))
   self.assertEqual(m.verify_download(p,digest,13),metadata)
 def test_expected_version_is_explicit_and_not_boolean_or_coerced(self):
  for v in [None,True,False,'13',0,-1,2100000001]:
   with self.subTest(v=v),self.assertRaises(ValueError):m.verify_download('/not-read', 'a'*64,v)
 def test_digest_is_exact_not_an_expression_or_coerced_value(self):
  for d in [None,True,'','A'*64,'a'*63,'a'*64+'\n','x;echo bad']:
   with self.subTest(d=d),self.assertRaises(ValueError):m.verify_download('/not-read',d,13)
 def test_strict_dispatch_inputs(self):
  self.assertEqual(m.validate_store_inputs('123','13','a'*64),('123',13,'a'*64))
  for i in [('', '13','a'*64),('1;echo bad','13','a'*64),('1','01','a'*64),('1','2100000001','a'*64),('1','13','*'),(True,'13','a'*64)]:
   with self.subTest(i=i),self.assertRaises(ValueError):m.validate_store_inputs(*i)
 def test_trusted_download_requires_same_revision_success_without_broader_trust(self):
  sha='a'*40;r={'status':'completed','conclusion':'success','event':'workflow_dispatch','head_sha':sha,'head_branch':'validation/isolated-current-native','path':'.github/workflows/passway-fresh-native-smoke.yml','head_repository':{'full_name':'Cynqra/passway-native-tests'}}
  m.verify_download_run(r,sha)
  for k,v in [('status','in_progress'),('conclusion','failure'),('event','pull_request'),('head_sha','b'*40),('head_branch','main'),('path','.github/workflows/untrusted.yml'),('head_repository',{'full_name':'fork/test'})]:
   with self.subTest(k=k),self.assertRaises(ValueError):m.verify_download_run({**r,k:v},sha)
 def test_untrusted_lookup_stops_before_artifact_download(self):
  from acquire_store_evidence import acquire
  from types import SimpleNamespace
  calls=[]
  def runner(args,**kwargs):calls.append(args);return SimpleNamespace(returncode=0,stdout='{}')
  with self.assertRaises(ValueError):acquire({'PASSWAY_STORE_DOWNLOAD_RUN_ID':'1','PASSWAY_STORE_VERSION_CODE':'13','PASSWAY_STORE_APK_SHA256':'a'*64,'GITHUB_SHA':'a'*40},runner)
  self.assertEqual(len(calls),1)
 def test_malformed_inputs_stop_before_any_network_lookup(self):
  from acquire_store_evidence import acquire
  def runner(*args,**kwargs):self.fail('No network for malformed input')
  with self.assertRaises(ValueError):acquire({},runner)
 def test_current_and_future_versions_keep_exact_hash_binding(self):
  for version in [12,13,14,2100000000]:
   with self.subTest(version=version),tempfile.TemporaryDirectory() as d:
    p=pathlib.Path(d);data=b'PK-exact-synthetic-fixture';(p/'passway-store-signed.apk').write_bytes(data);digest=hashlib.sha256(data).hexdigest();metadata={'package':'com.passway.app','versionCode':version,'bytes':len(data),'sha256':digest};(p/'download-verification.json').write_text(json.dumps(metadata));self.assertEqual(m.verify_download(p,digest,version),metadata)
    with self.assertRaises(ValueError):m.verify_download(p,'b'*64,version)
    metadata['bytes']=True;(p/'download-verification.json').write_text(json.dumps(metadata))
    with self.assertRaises(ValueError):m.verify_download(p,digest,version)
 def test_successful_evidence_acquisition_uses_bounded_argument_lists(self):
  import os
  from acquire_store_evidence import acquire
  from types import SimpleNamespace
  sha='a'*40;data=b'PK-exact-fixture';digest=hashlib.sha256(data).hexdigest();calls=[];r={'status':'completed','conclusion':'success','event':'workflow_dispatch','head_sha':sha,'head_branch':'validation/isolated-current-native','path':'.github/workflows/passway-fresh-native-smoke.yml','head_repository':{'full_name':'Cynqra/passway-native-tests'}}
  with tempfile.TemporaryDirectory() as tmp:
   def runner(args,**kwargs):
    calls.append((args,kwargs));self.assertNotIn('shell',kwargs)
    if args[:2]==['gh','api']:return SimpleNamespace(returncode=0,stdout=json.dumps(r))
    p=pathlib.Path('store-apk-results');p.mkdir();(p/'passway-store-signed.apk').write_bytes(data);(p/'download-verification.json').write_text(json.dumps({'package':'com.passway.app','versionCode':13,'sha256':digest,'bytes':len(data)}));return SimpleNamespace(returncode=0,stdout='')
   previous=os.getcwd()
   try:
    os.chdir(tmp);report=acquire({'PASSWAY_STORE_DOWNLOAD_RUN_ID':'123','PASSWAY_STORE_VERSION_CODE':'13','PASSWAY_STORE_APK_SHA256':digest,'GITHUB_SHA':sha},runner)
   finally:os.chdir(previous)
   self.assertEqual(report['versionCode'],13);self.assertEqual(len(calls),2);self.assertEqual(calls[0][1]['timeout'],40);self.assertEqual(calls[1][1]['timeout'],120)
 def test_workflow_has_no_historical_run_or_version_pin(self):
  workflow=(pathlib.Path(__file__).parents[2]/'.github/workflows/passway-fresh-native-smoke.yml').read_text();section=workflow.split('  store-release-offline-ui:',1)[1].split('  internal-sharing-candidate:',1)[0]
  self.assertNotIn('38898141494',section);self.assertNotIn('d9450fddf19c4e80866698f8858a4a6cdbb9cd3c',section);self.assertNotIn("read(),8)",section)
  self.assertIn('run: python3 harness/acquire_store_evidence.py',section);self.assertIn('apksigner',section);self.assertIn('verify_badging',section);self.assertIn('inputs.store_download_run_id',section);self.assertIn('inputs.store_apk_sha256',section)

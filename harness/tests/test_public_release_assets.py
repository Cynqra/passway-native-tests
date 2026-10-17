import pathlib,sys,unittest,tempfile,shutil,json
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
import public_store_assets as m
from play_api_access import SafeError
class StoreAssetsTests(unittest.TestCase):
 def test_eight_hash_pinned_approved_assets(self):
  assets=m.load_assets();self.assertEqual(len(assets),8)
 def test_changed_file_is_rejected_before_network(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/'assets';shutil.copytree(m.ROOT,root)
   (root/'app-icon-512.png').write_bytes(b'invalid')
   with self.assertRaises(SafeError):m.load_assets(root)
 def test_correct_upload_route_and_return_hash(self):
  assets=m.load_assets();calls=[]
  def upload(url,headers,data,error_observer=None):
   calls.append(url);self.assertIn('/upload/androidpublisher/v3/',url);self.assertNotIn('/images/',url)
   import hashlib
   return {'image':{'sha256':hashlib.sha256(data).hexdigest()}}
  result=m.stage_assets('https://androidpublisher.googleapis.com/androidpublisher/v3/applications/com.passway.app/edits/123/listings/en-US',dict(icon=[],featureGraphic=[],phoneScreenshots=[]),assets,{},upload)
  self.assertEqual(len(calls),8);self.assertEqual(len(result),8)
 def test_existing_unrelated_images_are_never_replaced(self):
  with self.assertRaises(SafeError):m.stage_assets('unused',dict(icon=[{'sha256':'unrelated'}],featureGraphic=[],phoneScreenshots=[]),m.load_assets(),{},lambda *a,**k:self.fail('Must not upload'))
 def test_exact_existing_images_are_not_duplicated(self):
  assets=m.load_assets();inventory={k:[{'sha256':r['sha256']} for r,d in assets if r['kind']==k] for k in ('icon','featureGraphic','phoneScreenshots')}
  self.assertEqual(m.stage_assets('unused',inventory,assets,{},lambda *a,**k:self.fail('Must not upload')),[])
 def test_unconfirmed_upload_hash_fails_without_retry(self):
  calls=[]
  def upload(*a,**k):calls.append(1);return {'image':{'sha256':'wrong'}}
  with self.assertRaises(SafeError):m.stage_assets('unused',dict(icon=[],featureGraphic=[],phoneScreenshots=[]),m.load_assets(),{},upload)
  self.assertEqual(len(calls),1)
 def test_upload_rejects_untrusted_host_before_network(self):
  with self.assertRaises(SafeError):m.upload_png('https://example.invalid',{},b'png')

import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
import download_store_apk as m
class StoreApkDownloadTests(unittest.TestCase):
 def test_only_registered_play_key_selected(self):
  j={'generatedApks':[{'certificateSha256Hash':'wrong','generatedUniversalApk':{'downloadId':'wrong'}},{'certificateSha256Hash':m.CERT.lower(),'generatedUniversalApk':{'downloadId':'expected'}}]}
  self.assertEqual(m.selection(j),'expected')
 def test_absent_ambiguous_or_wrong_key_rejected(self):
  k={'certificateSha256Hash':m.CERT,'generatedUniversalApk':{'downloadId':'expected'}}
  for j in [{},{'generatedApks':[k,k]},{'generatedApks':[{'certificateSha256Hash':'wrong'}]}]:
   with self.assertRaises(m.SafeError):m.selection(j)
 def test_no_universal_or_malformed_download_rejected(self):
  for x in [None,'','x\n',5]:
   with self.assertRaises(m.SafeError):m.selection({'generatedApks':[{'certificateSha256Hash':m.CERT,'generatedUniversalApk':{'downloadId':x}}]})

class StoreApkVersionBindingTests(unittest.TestCase):
 def test_current_and_future_numeric_versions_bind_actual_manifest(self):
  for code in [7,8,9,2100000000]:
   m.verify_badging("package: name='com.passway.app' versionCode='"+str(code)+"' versionName='0.3.2'",code)
 def test_wrong_package_or_version_and_missing_manifest_are_rejected(self):
  for text in ["", "package: name='other.app' versionCode='8'", "package: name='com.passway.app' versionCode='7'", "package: name='com.passway.app.evil' versionCode='8'"]:
   with self.subTest(text=text):
    with self.assertRaises(m.SafeError):m.verify_badging(text,8)
 def test_untrusted_expected_version_cannot_be_interpreted_as_shell_or_match_expression(self):
  for code in [None,True,0,-1,"8", "8;echo bad",2100000001]:
   with self.subTest(code=code):
    with self.assertRaises(m.SafeError):m.verify_badging("package: name='com.passway.app' versionCode='8'",code)

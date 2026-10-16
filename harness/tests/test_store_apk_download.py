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

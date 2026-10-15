import json,os,pathlib,runpy,subprocess,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[2]
class IsolatedNativeTests(unittest.TestCase):
 def test_real_service_environment_is_rejected_before_sdk_loading(self):
  base={**os.environ,'GCLOUD_PROJECT':'demo-passway','FIRESTORE_EMULATOR_HOST':'127.0.0.1:8080','FIREBASE_AUTH_EMULATOR_HOST':'127.0.0.1:9099'}
  for key,value in [('GCLOUD_PROJECT','real-project'),('FIRESTORE_EMULATOR_HOST','firestore.googleapis.com'),('FIREBASE_AUTH_EMULATOR_HOST','identitytoolkit.googleapis.com'),('GOOGLE_APPLICATION_CREDENTIALS','real-credentials.json'),('FIREBASE_SERVICE_ACCOUNT','not-a-real-key')]:
   with self.subTest(key=key):
    result=subprocess.run(['node',str(ROOT/'harness/isolated_api.cjs')],env={**base,key:value},capture_output=True,text=True,timeout=5)
    self.assertNotEqual(result.returncode,0);self.assertIn('Strict emulator isolation guard failed',result.stderr)
 def test_overlay_is_explicit_synthetic_and_hash_recorded(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);app=root/'validation-source/passway-app';(app/'src/firebase').mkdir(parents=True);(app/'plugins').mkdir()
   (app/'src/firebase/client.ts').write_text("import { getAuth } from '@react-native-firebase/auth';\nimport { getFirestore } from '@react-native-firebase/firestore';\nconst app = getApp();\nexport const auth = getAuth(app);\nexport const db = getFirestore(app);\n")
   (app/'app.config.ts').write_text("    '@react-native-firebase/app',\n");(app/'firebase.json').write_text('{}')
   cwd=pathlib.Path.cwd()
   try:os.chdir(root);runpy.run_path(str(ROOT/'harness/prepare_isolated_native.py'))
   finally:os.chdir(cwd)
   code=(app/'src/firebase/client.ts').read_text();self.assertIn("app.options.projectId !== 'demo-passway'",code);self.assertIn('10.0.2.2:9099',code);self.assertIn("'10.0.2.2', 8080",code)
   provenance=json.loads((root/'native-results/overlay-provenance.json').read_text());self.assertNotEqual(provenance['client_before_sha256'],provenance['client_after_sha256']);self.assertEqual(provenance['project'],'demo-passway');self.assertEqual(json.loads((app/'google-services.json').read_text())['project_info']['project_id'],'demo-passway')
if __name__=='__main__':unittest.main()

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
class ReadinessDeadlineTests(unittest.TestCase):
 def test_unavailable_service_is_bounded(self):
  import importlib.util,time
  spec=importlib.util.spec_from_file_location('isolated_readiness',ROOT/'harness/wait_isolated_services.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  started=time.monotonic()
  with patch.object(module.urllib.request,'urlopen',side_effect=TimeoutError('synthetic stall')):
   with self.assertRaises(TimeoutError):module.wait_ready('api',seconds=.03)
  self.assertLess(time.monotonic()-started,.5)
 def test_unknown_service_group_cannot_target_real_hosts(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('isolated_readiness',ROOT/'harness/wait_isolated_services.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with self.assertRaises(ValueError):module.wait_ready('production')
class AvdConfigurationTests(unittest.TestCase):
 def load_configure(self):
  return runpy.run_path(str(ROOT/'harness/configure_avd.py'))['configure']
 def test_selected_avd_only_is_configured(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   for name in ['passway-native','passway-isolated']:
    p=root/(name+'.avd');p.mkdir();(p/'config.ini').write_text('hw.lcd.density=420\nother=value\n')
   self.load_configure()(root,'passway-isolated')
   self.assertEqual((root/'passway-native.avd/config.ini').read_text(),'hw.lcd.density=420\nother=value\n')
   selected=(root/'passway-isolated.avd/config.ini').read_text()
   self.assertIn('hw.lcd.density=220',selected);self.assertIn('other=value',selected)
 def test_missing_avd_fails_instead_of_silent_success(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(FileNotFoundError):self.load_configure()(d,'missing')
 def test_unsafe_avd_name_is_rejected(self):
  with self.assertRaises(ValueError):self.load_configure()('/tmp','../other')
if __name__=='__main__':unittest.main()

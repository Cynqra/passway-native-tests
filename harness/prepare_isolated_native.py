"""Test-only overlay. Never ships or connects to a real Firebase project."""
import hashlib,json,pathlib
APP=pathlib.Path('validation-source/passway-app')
PROJECT='demo-passway'
config={'project_info':{'project_number':'123456789012','project_id':PROJECT,'storage_bucket':PROJECT+'.firebasestorage.app'},'client':[{'client_info':{'mobilesdk_app_id':'1:123456789012:android:abcdef0123456789','android_client_info':{'package_name':'com.passway.app'}},'api_key':[{'current_key':'AIza'+'A'*35}]}],'configuration_version':'1'}
(APP/'google-services.json').write_text(json.dumps(config))
firebase=json.loads((APP/'firebase.json').read_text());firebase['emulators']={'auth':{'host':'127.0.0.1','port':9099},'firestore':{'host':'127.0.0.1','port':8080},'ui':{'enabled':False},'singleProjectMode':True};(APP/'firebase.json').write_text(json.dumps(firebase,indent=2))
p=APP/'src/firebase/client.ts';original=p.read_text();s=original
for old,new in [
 ("import { getAuth } from '@react-native-firebase/auth';","import { getAuth, connectAuthEmulator } from '@react-native-firebase/auth';"),
 ("import { getFirestore } from '@react-native-firebase/firestore';","import { getFirestore, connectFirestoreEmulator } from '@react-native-firebase/firestore';"),
 ("const app = getApp();","const app = getApp();\nif (app.options.projectId !== 'demo-passway') throw new Error('Isolated test project guard failed.');"),
 ('export const auth = getAuth(app);',"export const auth = getAuth(app);\nconnectAuthEmulator(auth, 'http://10.0.2.2:9099');"),
 ('export const db = getFirestore(app);',"export const db = getFirestore(app);\nconnectFirestoreEmulator(db, '10.0.2.2', 8080);")]:
 if s.count(old)!=1:raise RuntimeError('Source overlay anchor changed; review required: '+old)
 s=s.replace(old,new)
p.write_text(s)
plugin=APP/'plugins/withIsolatedEmulators.cjs';plugin.write_text("const {withAndroidManifest}=require('@expo/config-plugins');module.exports=c=>withAndroidManifest(c,m=>{m.modResults.manifest.application[0].$['android:usesCleartextTraffic']='true';return m;});\n")
p=APP/'app.config.ts';s=p.read_text();anchor="    '@react-native-firebase/app',";assert s.count(anchor)==1;s=s.replace(anchor,"    './plugins/withIsolatedEmulators.cjs',\n"+anchor);p.write_text(s)
# No Expo project credentials or live push project may enter this fixture.
p=APP/'app.config.ts';s=p.read_text().replace("'d21f83c5-5e34-4a1c-9dea-346885668a27'","'00000000-0000-4000-8000-000000000000'").replace("'naveenbharti310s-team'","'isolated-test-only'");p.write_text(s)
pathlib.Path('native-results').mkdir(exist_ok=True)
pathlib.Path('native-results/overlay-provenance.json').write_text(json.dumps({'scope':'Current-source Android native UI plus Auth/Firestore emulators and original candidate HTTP handlers. Test-only emulator routing/cleartext overlay; no production backend, SMS or attestation proof.','project':PROJECT,'client_before_sha256':hashlib.sha256(original.encode()).hexdigest(),'client_after_sha256':hashlib.sha256((APP/'src/firebase/client.ts').read_bytes()).hexdigest(),'overlay_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()},indent=2))

import json,hashlib,zipfile,pathlib
j=json.loads(pathlib.Path('harness/candidate/provenance.json').read_text());bundle=pathlib.Path('harness/candidate/index.android.bundle').read_bytes();assert hashlib.sha256(bundle).hexdigest()==j['bundle_sha256']
with zipfile.ZipFile('universal.apk') as original,zipfile.ZipFile('candidate-unsigned.apk','w') as output:
 old=original.read('assets/index.android.bundle');assert old[:12]==bundle[:12], 'Hermes bytecode version mismatch'
 for item in original.infolist():
  if item.filename.startswith('META-INF/') and (item.filename.endswith(('.RSA','.DSA','.SF')) or item.filename=='META-INF/MANIFEST.MF'):continue
  output.writestr(item,bundle if item.filename=='assets/index.android.bundle' else original.read(item.filename))
with zipfile.ZipFile('universal.apk') as original,zipfile.ZipFile('candidate-unsigned.apk') as output:
 changed=[i for i in output.namelist() if output.read(i)!=original.read(i)]
 assert changed==['assets/index.android.bundle'],changed
j['changed_apk_entries']=changed;pathlib.Path('candidate-provenance.json').write_text(json.dumps(j,indent=2));print('Verified candidate: only JavaScript bytecode entry replaced; native files unchanged')

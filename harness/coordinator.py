import pathlib,subprocess,sys,time,os,shutil,json,xml.etree.ElementTree as ET
from status import publish,ROOT
end=time.monotonic()+1500
for attempt in range(1,6):
 os.environ['PASSWAY_ATTEMPT']=str(attempt);ROOT.mkdir(exist_ok=True,parents=True)
 publish('native_test_started')
 try:code=subprocess.run([sys.executable,'harness/native_e2e.py'],timeout=min(900,max(1,int(end-time.monotonic())))).returncode
 except subprocess.TimeoutExpired:code=124
 if code==0 and (ROOT/'complete.json').exists():publish('passed');sys.exit(0)
 details={'exit_code':code}
 if (ROOT/'location-diagnostics.txt').exists():details['location_diagnostics']=(ROOT/'location-diagnostics.txt').read_text()[-22000:]
 if (ROOT/'xml/failure.xml').exists():
  t=ET.parse(ROOT/'xml/failure.xml');details['visible_ui']=[{k:n.attrib.get(k,'') for k in ['resource-id','text','content-desc','class','bounds','visible-to-user']} for n in t.iter('node') if n.attrib.get('visible-to-user')=='true' and (n.attrib.get('text') or n.attrib.get('resource-id') or n.attrib.get('content-desc'))]
 if (ROOT/'screens/failure.png').exists():
  import base64
  details['screenshot_png_base64']=base64.b64encode((ROOT/'screens/failure.png').read_bytes()).decode()
 publish('waiting_for_harness_fix',**details)
 archive=pathlib.Path('native-attempts')/('attempt-'+str(attempt));archive.parent.mkdir(exist_ok=True);shutil.copytree(ROOT,archive,dirs_exist_ok=True)
 old=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();changed=False
 until=min(end,time.monotonic()+300)
 while time.monotonic()<until:
  subprocess.run(['git','fetch','--quiet','origin','main'],check=True)
  new=subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()
  if new!=old:
   subprocess.run(['git','checkout','origin/main','--','harness'],check=True)
   # Update HEAD without replacing the active emulator or its app data.
   subprocess.run(['git','update-ref','HEAD',new],check=True)
   subprocess.run(['bash','harness/probe/build.sh'],check=True)
   subprocess.run(['adb','install','--no-incremental','-r','harness/probe/probe.apk'],check=True)
   shutil.rmtree(ROOT);ROOT.mkdir();changed=True;break
  time.sleep(10)
 if not changed:publish('failed_no_patch_within_five_minutes',**details);sys.exit(1)
publish('failed_attempt_limit');sys.exit(1)

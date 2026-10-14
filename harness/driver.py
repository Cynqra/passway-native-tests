import subprocess,time,xml.etree.ElementTree as ET,re,json,pathlib,os,base64
ROOT=pathlib.Path(os.environ.get('PASSWAY_RESULTS','native-results'));ROOT.mkdir(exist_ok=True)
for d in ['screens','xml']:(ROOT/d).mkdir(exist_ok=True)
import shutil
A=shutil.which('adb') or 'adb'
def adb(*args,timeout=90):
 t=time.monotonic();r=subprocess.run([A,*map(str,args)],capture_output=True,timeout=timeout)
 if r.returncode:raise RuntimeError('adb '+str(args[:3])+': '+r.stderr.decode(errors='replace')[:500])
 return r.stdout.decode(errors='replace')
def shell(*args):return adb('shell',*args)
def probe(selector=None,action=None,value=''):
 uid=shell('am','get-current-user').strip();args=['shell','am','instrument','-w','--user',uid]
 if action:
  args+=['-e','action',action,'-e','selectorB64',base64.b64encode(selector.encode()).decode()]
  if action=='setText':args+=['-e','valueB64',base64.b64encode(value.encode()).decode()]
 t=time.monotonic();out=adb(*args,'com.passway.nativeprobe/.Probe',timeout=45)
 with (ROOT/'probe-timing.jsonl').open('a') as f:f.write(json.dumps({'action':action or 'read','selector':selector,'seconds':round(time.monotonic()-t,2)})+'\n')
 m=re.search(r'INSTRUMENTATION_RESULT: hierarchy=([^\r\n]+)',out)
 if not m or (action and 'action_result=performed' not in out):raise RuntimeError('Native probe failed at '+str(selector)+': '+out[:1200])
 raw=base64.b64decode(m.group(1)).decode();return ET.fromstring(raw),raw
def dump(label='current'):
 for attempt in range(5):
  tree,raw=probe()
  if len(list(tree.iter('node')))>2:
   (ROOT/'xml'/f'{label}.xml').write_text(raw);return tree
  time.sleep(.4)
 raise RuntimeError('Native UI tree remained empty after five fresh inspections')
def nodes(t):return [dict(n.attrib) for n in t.iter('node')]
def match(n,s):return n.get('resource-id')==s or n.get('resource-id','').endswith(':id/'+s) or n.get('text')==s or n.get('content-desc')==s
def find(s,tree=None):
 t=tree if tree is not None else dump()
 return next((n for n in nodes(t) if match(n,s)),None)
def tapnode(n):
 s=n.get('resource-id') or n.get('text') or n.get('content-desc');probe(s,'touch');time.sleep(.5)
def tap(s,scroll=True):
 for _ in range(7 if scroll else 1):
  n=find(s)
  if n is not None and n.get('visible-to-user')=='true' and n.get('enabled')=='true':tapnode(n);return
  if scroll:shell('input','swipe','270','970','270','380','450');time.sleep(.7)
 raise RuntimeError('Visible actionable control not found: '+s)
def fill(s,value):
 tap(s);probe(s,'setText',value);time.sleep(.5)
 for attempt in range(4):
  t=dump();n=find(s,t)
  if s=='code-box-0':actual=''.join((find('code-box-'+str(i),t) or {}).get('text','') for i in range(4))
  else:actual=(n or {}).get('text','')
  if actual==value:return
  time.sleep(.5)
 raise RuntimeError('Native input readback mismatch at '+s+' after four fresh snapshots')
def back():shell('input','keyevent','KEYCODE_BACK');time.sleep(.7)
def shot(name):
 p=ROOT/'screens'/f'{name}.png';r=subprocess.run([A,'exec-out','screencap','-p'],capture_output=True,timeout=30)
 if r.returncode or not r.stdout.startswith(b'\x89PNG'):raise RuntimeError('Screenshot failed')
 p.write_bytes(r.stdout);return str(p)
def waitfor(s,seconds=90):
 until=time.monotonic()+seconds
 while time.monotonic()<until:
  tree=dump();n=find(s,tree)
  if n is not None:return n
  if s=='code-text' and find('Something went wrong. Try again.',tree) is not None:raise RuntimeError('Native generation returned app error: Something went wrong. Try again.')
  time.sleep(2)
 shot('timeout-'+re.sub('[^a-zA-Z0-9]','-',s));raise RuntimeError('Timed out waiting for '+s)
def record(name,status,detail=''):
 p=ROOT/'results.json';rs=json.loads(p.read_text()) if p.exists() else [];rs.append({'test':name,'status':status,'detail':detail,'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())});p.write_text(json.dumps(rs,indent=2));print(name,status,detail,flush=True)
 from status import publish
 publish(name,status=status)

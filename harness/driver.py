import subprocess,time,xml.etree.ElementTree as ET,re,json,pathlib,os,base64
ROOT=pathlib.Path(os.environ.get('PASSWAY_RESULTS','native-results'));ROOT.mkdir(exist_ok=True)
for d in ['screens','xml']:(ROOT/d).mkdir(exist_ok=True)
import shutil
from contextlib import contextmanager
from contextvars import ContextVar
_DEADLINE = ContextVar("native_deadline",default=None)
def remaining_timeout(limit):
 end=_DEADLINE.get()
 if end is None:return limit
 remaining=end-time.monotonic()
 if remaining<=0:raise TimeoutError("Native operation exceeded its deadline")
 return min(limit,remaining)
@contextmanager
def deadline(seconds):
 previous=_DEADLINE.get()
 token=_DEADLINE.set(min(previous,time.monotonic()+seconds) if previous is not None else time.monotonic()+seconds)
 try:yield
 finally:_DEADLINE.reset(token)
A=shutil.which('adb') or 'adb'
def adb(*args,timeout=90):
 t=time.monotonic();r=subprocess.run([A,*map(str,args)],capture_output=True,timeout=remaining_timeout(timeout))
 if r.returncode:raise RuntimeError('adb '+str(args[:3])+': '+r.stderr.decode(errors='replace')[:500])
 return r.stdout.decode(errors='replace')
def shell(*args):return adb('shell',*args)
class TargetUnavailableBeforeDispatch(RuntimeError):
 """Native probe explicitly confirms no target/action dispatch occurred."""
 pass

def probe(selector=None,action=None,value=''):
 uid=shell('am','get-current-user').strip();args=['shell','am','instrument','-w','--user',uid]
 if action:
  args+=['-e','action',action,'-e','selectorB64',base64.b64encode(selector.encode()).decode()]
  if action=='setText':args+=['-e','valueB64',base64.b64encode(value.encode()).decode()]
 t=time.monotonic();out=adb(*args,'com.passway.nativeprobe/.Probe',timeout=45)
 with (ROOT/'probe-timing.jsonl').open('a') as f:f.write(json.dumps({'action':action or 'read','selector':selector,'seconds':round(time.monotonic()-t,2)})+'\n')
 m=re.search(r'INSTRUMENTATION_RESULT: hierarchy=([^\r\n]+)',out)
 if action=='touch' and 'action_result=performed' not in out and re.search(r'^INSTRUMENTATION_RESULT: probe_error=java\.lang\.Exception: Visible action target missing: '+re.escape(selector or '')+r'\r?$',out,re.M):
  raise TargetUnavailableBeforeDispatch('Visible action target missing before dispatch: '+str(selector))
 if not m or (action and 'action_result=performed' not in out):raise RuntimeError('Native probe failed at '+str(selector)+': '+out[:1200])
 raw=base64.b64decode(m.group(1)).decode();return ET.fromstring(raw),raw
def dump(label='current'):
 with deadline(30):
  for attempt in range(5):
   tree,raw=probe()
   if len(list(tree.iter('node')))>2:
    (ROOT/'xml'/f'{label}.xml').write_text(raw);return tree
   time.sleep(min(.4,remaining_timeout(.4)))
  raise RuntimeError('Native UI tree remained empty after five fresh inspections')
def nodes(t):return [dict(n.attrib) for n in t.iter('node')]
def match(n,s):return n.get('resource-id')==s or n.get('resource-id','').endswith(':id/'+s) or n.get('text')==s or n.get('content-desc')==s
def find(s,tree=None):
 t=tree if tree is not None else dump()
 return next((n for n in nodes(t) if match(n,s)),None)
def tapnode(n):
 s=n.get('resource-id') or n.get('text') or n.get('content-desc')
 # Probe already waits for dispatch and returns a fresh post-action hierarchy.
 tree,_=probe(s,'touch');return tree
def swipe_viewport(tree):
 # Prefer the smallest visible vertical scroll surface. A display-wide
 # gesture can start on fixed bottom navigation and never reach the form.
 # Use only observed bounds; retain the display fallback for legacy trees.
 def bounds(node):
  values=re.findall(r'-?\d+',node.get('bounds',''))
  if len(values)!=4:return None
  l,t,r,b=map(int,values)
  return (l,t,r,b) if r-l>=100 and b-t>=100 else None
 surfaces=[bounds(n) for n in tree.iter('node') if n.get('class')=='android.widget.ScrollView' and n.get('visible-to-user')=='true']
 surfaces=[b for b in surfaces if b is not None]
 root=next(tree.iter('node'),None)
 viewport=min(surfaces,key=lambda b:(b[2]-b[0])*(b[3]-b[1])) if surfaces else (bounds(root) if root is not None else None)
 if viewport is None:raise RuntimeError('Cannot scroll without valid observed viewport bounds')
 left,top,right,bottom=viewport;width=right-left;height=bottom-top
 shell('input','swipe',str(left+width//2),str(top+int(height*.8)),str(left+width//2),str(top+int(height*.3)),'450')
def tap(s,scroll=True):
 # A fresh inspection does not make a later accessibility node immutable.
 # Reacquire only the probe's explicit pre-dispatch missing-target condition.
 # Never retry rejected/uncertain injection or a performed action.
 missing=0
 with deadline(30):
  for _ in range(7 if scroll else 3):
   tree=dump();n=find(s,tree)
   if n is not None and n.get('visible-to-user')=='true' and n.get('enabled')=='true':
    try:return tapnode(n)
    except TargetUnavailableBeforeDispatch:
     missing+=1
     with (ROOT/'pre-dispatch-reacquisition.jsonl').open('a') as f:f.write(json.dumps({'selector':s,'attempt':missing,'actionDispatched':False})+'\n')
     if missing>=3:raise
     time.sleep(remaining_timeout(.2));continue
   if scroll:swipe_viewport(tree);time.sleep(remaining_timeout(.7))
 raise RuntimeError('Visible actionable control not found: '+s)
def fill(s,value):
 tap(s);t,_=probe(s,'setText',value)
 # Verify the actual post-setText hierarchy, never the pre-touch tree. Keep
 # all four fresh-read retries for asynchronously committed native input.
 def matches(t):
  if s=='code-box-0':actual=''.join((find('code-box-'+str(i),t) or {}).get('text','') for i in range(4))
  else:actual=(find(s,t) or {}).get('text','')
  return actual==value
 if matches(t):return
 for attempt in range(4):
  time.sleep(min(.5,remaining_timeout(.5)))
  if matches(dump()):return
 raise RuntimeError('Native input readback mismatch at '+s+' after post-action snapshot and four fresh retries')
def back():shell('input','keyevent','KEYCODE_BACK');time.sleep(.7)
def shot(name):
 p=ROOT/'screens'/f'{name}.png';r=subprocess.run([A,'exec-out','screencap','-p'],capture_output=True,timeout=remaining_timeout(30))
 if r.returncode or not r.stdout.startswith(b'\x89PNG'):raise RuntimeError('Screenshot failed')
 p.write_bytes(r.stdout);return str(p)
def waitfor(s,seconds=90):
 # Nested ADB/probe calls share this budget; an inner 45s timeout must not
 # extend a caller's 5s/20s wait into minutes. Preserve original exceptions.
 with deadline(seconds):
  while True:
   tree=dump();n=find(s,tree)
   if n is not None and n.get('visible-to-user')=='true':return n
   if s=='code-text' and find('Something went wrong. Try again.',tree) is not None:raise RuntimeError('Native generation returned app error: Something went wrong. Try again.')
   time.sleep(remaining_timeout(2))
def record(name,status,detail=''):
 p=ROOT/'results.json';rs=json.loads(p.read_text()) if p.exists() else [];rs.append({'test':name,'status':status,'detail':detail,'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())});p.write_text(json.dumps(rs,indent=2));print(name,status,detail,flush=True)
 from status import publish
 publish(name,status=status)

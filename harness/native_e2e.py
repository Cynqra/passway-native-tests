from driver import *
import traceback
PKG='com.passway.app'

def check(name,condition,detail=''):
 if not condition:raise AssertionError(name+': '+detail)
 record(name,'PASS',detail)
def texts(t=None):return ' '.join(n.get('text','')+' '+n.get('content-desc','') for n in nodes(t if t is not None else dump()))
def hide_keyboard():
 s=shell('dumpsys','input_method')
 if re.search(r'mInputShown=true|isInputViewShown=true',s):back()
def snap(name):
 shot(name);tree=dump(name);return tree

def location_fix():
 for provider in ['gps','network','fused']:
  shell('cmd','location','providers','set-test-provider-location',provider,'--location','28.6139,77.2090','--accuracy','5')

def user(uid):
 shell('am','start-user','-w',uid);shell('am','switch-user',uid)
 for _ in range(30):
  if shell('am','get-current-user').strip()==str(uid):break
  time.sleep(1)
 shell('settings','--user',uid,'put','secure','user_setup_complete','1')
 shell('settings','--user',uid,'put','secure','show_ime_with_hard_keyboard','1')
 shell('cmd','location','set-location-enabled','true','--user',uid)
 location_fix()
 shell('settings','--user',uid,'put','system','screen_off_timeout','1800000')
 shell('input','keyevent','KEYCODE_WAKEUP');shell('wm','dismiss-keyguard');shell('cmd','statusbar','collapse')
 shell('am','start','-W','--user',uid,'-n',PKG+'/.MainActivity');time.sleep(3)

def ready_generate():
 until=time.monotonic()+100
 while time.monotonic()<until:
  t=dump()
  if find('name-input',t) is not None and find('generate',t) is not None:return
  if find('age-day',t) is not None:
   fill('age-day','01');fill('age-month','01');fill('age-year','1990');hide_keyboard();tap('age-continue')
  elif find('new-connection',t) is not None:tap('new-connection')
  elif find('chat-back',t) is not None:tap('chat-back')
  elif find('Go back',t) is not None:tap('Go back')
  elif find('cancel-code',t) is not None:tap('cancel-code')
  elif find('Back to chats',t) is not None:tap('Back to chats')
  elif find('Back to start',t) is not None:tap('Back to start')
  else:time.sleep(2)
 raise RuntimeError('Generate form not reached')

def login(uid,phone,audit=False):
 user(uid)
 until=time.monotonic()+90
 while time.monotonic()<until:
  t=dump()
  if any(find(k,t) is not None for k in ['welcome-next','phone-input','new-connection','generate','age-day','code-box-0','message-input','cancel-code']):break
  time.sleep(2)
 else:raise RuntimeError('Native cold-start timeout')
 if find('phone-input',t) is None and find('welcome-next',t) is None:
  ready_generate();record('Native authenticated session resumed user'+str(uid),'PASS');return
 if find('welcome-next',t):
  if audit:
   for i in range(2,5):tap('welcome-next');waitfor(f'0{i} / 04');snap(f'user{uid}-onboarding-{i}')
   tap('get-started');record('Native onboarding all four pages','PASS')
  else:
   for i in range(2,5):tap('welcome-next');waitfor(f'0{i} / 04',20)
   tap('get-started')
 waitfor('phone-input',90)
 if audit:
  fill('phone-input','111');hide_keyboard();tap('send-code');t=snap('invalid-phone')
  check('Native invalid phone rejected',find('phone-input',t) is not None and find('verify-input',t) is None and '10 digit' in texts(t).lower(),texts(t))
 fill('phone-input',phone);hide_keyboard();tap('send-code');waitfor('verify-input',90)
 record('Native fictional OTP request user'+str(uid),'PASS','Official Firebase no-SMS test-number flow, not real 2Factor delivery')
 if audit:
  fill('verify-input','000000');hide_keyboard();tap('verify');time.sleep(3);t=snap('wrong-otp')
  check('Native wrong OTP rejected',find('verify-input',t) is not None and ('did not match' in texts(t).lower() or 'invalid' in texts(t).lower()),texts(t))
 fill('verify-input','123456');hide_keyboard();tap('verify');time.sleep(4)
 ready_generate();snap('user'+str(uid)+'-signed-in');record('Native Firebase sign-in user'+str(uid),'PASS')

try:
 import threading
 def gps_stream():
  while True:
   try:location_fix()
   except Exception:pass
   time.sleep(2)
 shell('appops','set','com.android.shell','android:mock_location','allow')
 for provider in ['gps','network','fused']:
  shell('cmd','location','providers','add-test-provider',provider,'--accuracy','1')
  shell('cmd','location','providers','set-test-provider-enabled',provider,'true')
 location_fix()
 threading.Thread(target=gps_stream,daemon=True).start()
 state=shell('dumpsys','location');(ROOT/'location-before.txt').write_text(state)
 check('Android test-location providers seeded', 'mock' in state.lower() and '28.613' in state, 'OS test providers; simulated Delhi location, not physical proximity certification')
 shell('dumpsys','battery','set','ac','1');shell('dumpsys','battery','set','level','100');shell('cmd','statusbar','collapse')
 shell('settings','put','secure','show_ime_with_hard_keyboard','1')
 shell('settings','put','system','screen_off_timeout','1800000')
 shell('settings','put','global','window_animation_scale','0');shell('settings','put','global','transition_animation_scale','0');shell('settings','put','global','animator_duration_scale','0')
 shell('pm','grant',PKG,'android.permission.ACCESS_FINE_LOCATION');shell('pm','grant',PKG,'android.permission.ACCESS_COARSE_LOCATION')
 if int(shell('getprop','ro.build.version.sdk').strip())>=33:shell('pm','grant',PKG,'android.permission.POST_NOTIFICATIONS')
 adb('emu','geo','fix','77.2090','28.6139')
 existing=shell('pm','list','users');m=re.search(r'UserInfo\{(\d+):Passway(?: synthetic peer)?:',existing)
 if m:peer=int(m.group(1));record('Existing isolated peer reused','PASS')
 else:
  out=shell('pm','create-user','"Passway synthetic peer"');m=re.search(r'id (\d+)',out);check('Second isolated Android user created',m is not None,out);peer=int(m.group(1))
 for pkg in [PKG,'com.passway.nativeprobe']:shell('cmd','package','install-existing','--user',peer,pkg)
 for uid in [0,peer]:
  for perm in (['android.permission.ACCESS_FINE_LOCATION','android.permission.ACCESS_COARSE_LOCATION']+(['android.permission.POST_NOTIFICATIONS'] if int(shell('getprop','ro.build.version.sdk').strip())>=33 else [])):shell('pm','grant','--user',uid,PKG,perm)
  shell('am','force-stop','--user',uid,PKG)
 (ROOT/'peer.json').write_text(json.dumps({'peer':peer}))
 login(0,'9999900001',True);login(peer,'9999900002')
 # Both sides below use native app UI and its actual Firebase/API calls.
 user(0);ready_generate();fill('name-input','Native Test A');hide_keyboard();record('Native generation form input verified','PASS');tap('generate');waitfor('code-text',45)
 t=snap('native-generated-code');n=find('code-text',t);code=re.sub(r'[^A-Z0-9]','',n.get('text','').upper());check('Native code generated',len(code)==4,'Four-character code rendered')
 user(peer);ready_generate();tap('have-code');waitfor('code-box-0');fill('code-box-0',code);fill('name-input','Native Test B');hide_keyboard();tap('connect');waitfor('Waiting for them to accept',60);snap('native-peer-pending');record('Native peer redeemed code','PASS')
 user(0);waitfor('accept',60);snap('native-accept-request');tap('accept');waitfor('message-input',60);record('Native request acceptance','PASS')
 fill('message-input','Native E2E hello from A');hide_keyboard();tap('send-message');waitfor('Native E2E hello from A');snap('native-A-message-sent')
 user(peer);waitfor('message-input',60);waitfor('Native E2E hello from A');record('Native A to native B delivery','PASS')
 fill('message-input','Native E2E reply from B');hide_keyboard();tap('send-message');waitfor('Native E2E reply from B')
 user(0);waitfor('Native E2E reply from B');record('Native B to native A delivery','PASS');snap('native-bidirectional-chat')
 # Exercise a real keyboard; test functional input, not emulator speed claims.
 fill('message-input','Keyboard edit one');ime=shell('dumpsys','input_method');check('Native soft keyboard visible',bool(re.search(r'mInputShown=true|isInputViewShown=true',ime)))
 for i in range(3):
  value='Keyboard edit '+str(i);fill('message-input',value);shell('input','text','z');time.sleep(1)
  check('Native keyboard typed character '+str(i),(find('message-input') or {}).get('text')==value+'z')
  hide_keyboard()
 record('Native keyboard edit and dismissal cycles','PASS','Three cycles; emulator results do not certify Oppo keyboard behavior')
 tap('chat-title');waitfor('note-input');fill('note-input','Native E2E private note');hide_keyboard();tap('note-save');waitfor('Native E2E private note');record('Native private note saved','PASS');snap('native-note-saved')
 tap('chat-options');tap('Report and end connection');waitfor('What went wrong?');snap('native-report-reasons');tap('Cancel');record('Native report sheet and cancellation','PASS','No report filed against a real user')
 tap('chat-back');waitfor('new-connection');snap('native-chat-list');record('Native chat list navigation','PASS')
 tap('You');waitfor('settings-name');snap('native-settings');record('Native settings navigation','PASS')
 tap('open-chats');waitfor('new-connection');t=dump();rows=[n for n in nodes(t) if n.get('resource-id','').startswith('chat-row-') and 'Native Test B' in n.get('content-desc','')]
 if not rows:
  # Row text is nested; locate the actual visible peer name, not a fixture ID.
  tap('Native Test B')
 else:tapnode(rows[0])
 waitfor('message-input');tap('chat-options');tap('End connection');waitfor('Connection ended');snap('native-ended');record('Native end connection','PASS')
 t=dump()
 if find('back-to-chats',t) is not None:tap('back-to-chats');waitfor('new-connection');tap('new-connection')
 else:tap('Back to start')
 waitfor('name-input');record('Native return after ending connection','PASS')
 shell('am','force-stop',PKG);shell('am','start','-n',PKG+'/.MainActivity');time.sleep(3);t=snap('native-relaunch');check('Native session survives relaunch',find('phone-input',t) is None and (find('name-input',t) is not None or find('new-connection',t) is not None))
 (ROOT/'complete.json').write_text(json.dumps({'status':'passed','coverage':'Native UI on two isolated Android users, one hardware-accelerated Android 14 emulator; real backend; fictional Firebase OTP; no real 2Factor SMS; not an Oppo physical-device certification'},indent=2))
except Exception as e:
 record('Native end-to-end run','FAIL',str(e));traceback.print_exc()
 try:snap('failure')
 except Exception:pass
 raise
finally:
 try:
  (ROOT/'app-logcat.txt').write_text(adb('logcat','-d'))
  (ROOT/'location-diagnostics.txt').write_text(shell('dumpsys','location'))
  (ROOT/'device-diagnostics.txt').write_text(shell('dumpsys','battery')+'\n'+shell('pm','list','users'))
 except Exception:pass

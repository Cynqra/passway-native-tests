"""Observed small-display/large-text native pairing; no production services."""
import json, re
from driver import ROOT, shell, fill, tap, tapnode, waitfor, find, dump, swipe_viewport, record

def visible_single_line(tree, selector, max_height):
 # Accessible button names can precede their TextView in the hierarchy.
 # Measure actual text, not the entire pill's padded touch target.
 node=next((dict(n.attrib) for n in tree.iter('node') if n.get('text')==selector),None) or find(selector,tree)
 if node is None or node.get('visible-to-user')!='true':return False
 b=list(map(int,re.findall(r'-?\d+',node.get('bounds',''))))
 return len(b)==4 and b[2]>b[0] and 0<b[3]-b[1]<=max_height

def run(ctx, peer):
 user, ready, hide, snap, check = (ctx[x] for x in ['user','ready_generate','hide_keyboard','snap','check'])
 previous={uid:shell('settings','--user',uid,'get','system','font_scale').strip() for uid in [0,peer]}
 try:
  shell('wm','size','440x880')
  for uid in [0,peer]:shell('settings','--user',uid,'put','system','font_scale','2.0')
  observed=shell('wm','size');(ROOT/'accessibility-display.txt').write_text(observed)
  check('Native accessibility uses observed 440x880 override and font scale2',
        'Override size: 440x880' in observed and all(float(shell('settings','--user',uid,'get','system','font_scale').strip())==2.0 for uid in [0,peer]))
  user(0);ready();tree=dump()
  check('Native large-text bottom navigation labels remain complete single lines',all(visible_single_line(tree,label,70) for label in ['Connect','Chats','You']))
  fill('name-input','Accessibility Test A');hide();tap('generate');waitfor('code-text',45)
  tree=snap('accessibility-large-code');code=find('code-text',tree)['text'].strip()
  check('Native large-text code and cancellation remain reachable',len(code)==4 and (find('cancel-code',tree) or {}).get('visible-to-user')=='true')
  check('Native full four-character code stays on one visible line',visible_single_line(tree,'code-text',120))
  user(peer);ready();tap('have-code');waitfor('code-box-0');fill('code-box-0',code);fill('name-input','Accessibility Peer Very Long');hide();tap('connect');waitfor('Waiting for them to accept',45)
  user(0)
  for _ in range(8):
   tree=dump();node=find('accept',tree)
   if node is not None and node.get('visible-to-user')=='true' and node.get('enabled')=='true':break
   swipe_viewport(tree)
  else:raise AssertionError('Large-text Accept cannot be reached by scrolling')
  tree=snap('accessibility-large-request')
  check('Native large-text consent labels remain complete single lines',all(visible_single_line(tree,label,80) for label in ['Accept','Decline']))
  tapnode(node);waitfor('message-input',45)
  record('Native small-display large-text request accepted','PASS','Actual Android440x880 override at density220 with both profiles fontScale2; real isolated pairing; screenshot retained')
  tap('chat-options');tap('End connection');waitfor('Connection ended',45);ready()
  (ROOT/'accessibility-complete.json').write_text(json.dumps({'passed':True,'displayOverride':'440x880','fontScale':2.0,'scope':'One observed emulator layout and actual pairing; not physical-device, TalkBack or exhaustive accessibility certification'},indent=2))
 finally:
  shell('wm','size','reset')
  for uid,value in previous.items():shell('settings','--user',uid,'put','system','font_scale',value if value not in ['null',''] else '1.0')

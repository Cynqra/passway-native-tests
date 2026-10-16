import importlib.util, pathlib, tempfile, types, sys, unittest, subprocess
from unittest.mock import patch
HARNESS=pathlib.Path(__file__).resolve().parents[1]
def load(name):
 spec=importlib.util.spec_from_file_location(name,HARNESS/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class HarnessTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=pathlib.Path(self.tmp.name)
  self.env=patch.dict('os.environ',{'PASSWAY_RESULTS':str(self.root)});self.env.start();self.addCleanup(self.env.stop)
  self.status=types.ModuleType('status');self.status.ROOT=self.root;self.status.publish=lambda *a,**k:None
  self.modules=patch.dict(sys.modules,{'status':self.status});self.modules.start();self.addCleanup(self.modules.stop)
 def test_nested_adb_timeout_is_capped_to_outer_budget(self):
  d=load('driver')
  with patch.object(d.time,'monotonic',return_value=100),patch.object(d.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=b'ok',stderr=b'')) as run:
   with d.deadline(3):
    with d.deadline(30):d.adb('shell','true',timeout=90)
   self.assertEqual(run.call_args.kwargs['timeout'],3)
 def test_expired_budget_does_not_start_adb(self):
  d=load('driver')
  with patch.object(d.time,'monotonic',return_value=100),patch.object(d.subprocess,'run') as run:
   with d.deadline(0):
    with self.assertRaises(TimeoutError):d.adb('shell','true')
   run.assert_not_called()
 def test_deadline_restored_after_exception(self):
  d=load('driver')
  with self.assertRaises(ValueError):
   with d.deadline(1):raise ValueError('test')
  self.assertIsNone(d._DEADLINE.get())
 def test_hidden_control_is_not_a_successful_wait(self):
  d=load('driver');tree=d.ET.fromstring('<hierarchy><node text="target" visible-to-user="false"/></hierarchy>')
  with patch.object(d,'dump',return_value=tree),patch.object(d.time,'sleep',side_effect=TimeoutError):
   with self.assertRaises(TimeoutError):d.waitfor('target',1)
 def test_coordinator_removes_stale_success_and_never_waits_for_patch(self):
  c=load('coordinator');(self.root/'complete.json').write_text('{}')
  with patch.object(c.subprocess,'run',return_value=types.SimpleNamespace(returncode=1)) as run:
   self.assertEqual(c.main(),1);self.assertEqual(run.call_count,1)
  self.assertFalse((self.root/'complete.json').exists())
 def test_exit_zero_without_fresh_marker_is_failure(self):
  c=load('coordinator')
  with patch.object(c.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)):
   self.assertEqual(c.main(),1)
 def test_fresh_success_marker_and_exit_zero_pass(self):
  c=load('coordinator')
  def finish(*a,**k):(self.root/'complete.json').write_text('{}');return types.SimpleNamespace(returncode=0)
  with patch.object(c.subprocess,'run',side_effect=finish):self.assertEqual(c.main(),0)
 def test_native_timeout_fails_without_retry(self):
  c=load('coordinator')
  with patch.object(c.subprocess,'run',side_effect=subprocess.TimeoutExpired('native',900)) as run:
   self.assertEqual(c.main(),124);self.assertEqual(run.call_count,1)
 def test_status_publishing_never_calls_github(self):
  status=load('status')
  with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
   status.publish('test_completed',exit_code=0)
  import json
  self.assertEqual(json.loads((self.root/'status.json').read_text())['stage'],'test_completed')
  self.assertEqual(len((self.root/'stages.jsonl').read_text().splitlines()),1)
  self.assertFalse((self.root/'status.json.tmp').exists())
 def test_real_subprocess_is_killed_at_outer_deadline(self):
  import time
  d=load('driver');d.A=sys.executable;started=time.monotonic()
  with d.deadline(.15):
   with self.assertRaises(subprocess.TimeoutExpired):d.adb('-c','import time;time.sleep(5)',timeout=90)
  self.assertLess(time.monotonic()-started,2)
 def test_deadlines_do_not_leak_to_background_thread(self):
  import threading
  d=load('driver');values=[]
  with d.deadline(0):
   t=threading.Thread(target=lambda:values.append(d.remaining_timeout(45)));t.start();t.join()
  self.assertEqual(values,[45])
 def test_standard_isolated_run_keeps_one_bounded_attempt(self):
  c=load('isolated_coordinator')
  with patch.dict('os.environ',{'PASSWAY_NATIVE_EXTENDED':'0'}),patch.object(c.subprocess,'run',return_value=types.SimpleNamespace(returncode=1)) as run:
   self.assertEqual(c.main(),1);self.assertEqual(run.call_count,1)
   self.assertEqual(run.call_args.kwargs['timeout'],900)
 def test_extended_run_requires_its_own_fresh_success_marker(self):
  c=load('isolated_coordinator');(self.root/'extended-complete.json').write_text('{}')
  def finish(*a,**k):(self.root/'complete.json').write_text('{}');return types.SimpleNamespace(returncode=0)
  with patch.dict('os.environ',{'PASSWAY_NATIVE_EXTENDED':'1'}),patch.object(c.subprocess,'run',side_effect=finish) as run:
   self.assertEqual(c.main(),1);self.assertEqual(run.call_count,1)
   self.assertEqual(run.call_args.kwargs['timeout'],1500)
  self.assertFalse((self.root/'extended-complete.json').exists())
 def tree(self,d,text='value'):
  return d.ET.fromstring('<hierarchy><node resource-id="field" text="'+text+'" visible-to-user="true" enabled="true"/></hierarchy>')
 def test_tapnode_returns_fresh_post_action_snapshot_without_duplicate_sleep(self):
  d=load('driver');t=self.tree(d)
  with patch.object(d,'probe',return_value=(t,'fresh')) as probe,patch.object(d.time,'sleep') as sleep:
   self.assertIs(d.tapnode({'resource-id':'field'}),t);probe.assert_called_once_with('field','touch');sleep.assert_not_called()
 def test_tap_returns_post_action_snapshot(self):
  d=load('driver');t=self.tree(d);n={'resource-id':'field','visible-to-user':'true','enabled':'true'}
  with patch.object(d,'find',return_value=n),patch.object(d,'tapnode',return_value=t):self.assertIs(d.tap('field'),t)
 def test_fill_verifies_fresh_settext_snapshot_without_redundant_read_or_sleep(self):
  d=load('driver');t=self.tree(d)
  with patch.object(d,'tap'),patch.object(d,'probe',return_value=(t,'fresh')) as probe,patch.object(d,'dump',side_effect=AssertionError('Unnecessary read')),patch.object(d.time,'sleep') as sleep:
   d.fill('field','value');probe.assert_called_once_with('field','setText','value');sleep.assert_not_called()
 def test_fill_refreshes_after_post_action_text_mismatch(self):
  d=load('driver');wrong=self.tree(d,'pending');right=self.tree(d)
  with patch.object(d,'tap'),patch.object(d,'probe',return_value=(wrong,'fresh')),patch.object(d,'dump',return_value=right) as dump,patch.object(d.time,'sleep'):
   d.fill('field','value');dump.assert_called_once()
 def test_fill_never_accepts_pre_action_snapshot(self):
  d=load('driver');right=self.tree(d);wrong=self.tree(d,'unchanged')
  with patch.object(d,'tap',return_value=right),patch.object(d,'probe',return_value=(wrong,'fresh')),patch.object(d,'dump',return_value=wrong) as dump,patch.object(d.time,'sleep'):
   with self.assertRaises(RuntimeError):d.fill('field','value')
   self.assertEqual(dump.call_count,4)
 def test_fill_split_code_readback_uses_fresh_action_snapshot(self):
  d=load('driver');t=d.ET.fromstring('<hierarchy>'+''.join('<node resource-id="code-box-'+str(i)+'" text="'+c+'"/>' for i,c in enumerate('AB12'))+'</hierarchy>')
  with patch.object(d,'tap'),patch.object(d,'probe',return_value=(t,'fresh')),patch.object(d,'dump',side_effect=AssertionError('Unnecessary read')),patch.object(d.time,'sleep'):
   d.fill('code-box-0','AB12')
 def test_isolated_revisions_do_not_serialize_but_release_modes_keep_shared_key(self):
  text=(HARNESS.parent/'.github/workflows/passway-fresh-native-smoke.yml').read_text()
  group=next(line for line in text.splitlines() if line.startswith('  group:'))
  self.assertIn("(inputs.mode == 'isolated-native' || inputs.mode == 'isolated-extended' || inputs.mode == '') && format('{0}-api{1}', github.sha, inputs.android_api_level || '36') || 'shared-release'",group)
  self.assertIn('  cancel-in-progress: false',text)
  for cloud_mode in ['internal-candidate','signed-release','play-api-check','store-apk-download']:
   self.assertNotIn("inputs.mode == '"+cloud_mode+"'",group)
 def test_current_source_android_api_choices_are_explicit_and_runtime_checked(self):
  text=(HARNESS.parent/'.github/workflows/passway-fresh-native-smoke.yml').read_text()
  self.assertIn("android_api_level:\n",text)
  self.assertIn("options: ['34', '35', '36']",text)
  self.assertIn("api-level: ${{ inputs.android_api_level || '36' }}",text)
  self.assertIn('test \"$actual_api\" = \"$PASSWAY_EXPECTED_ANDROID_API\"',text)
  self.assertIn('native-results/android-api.txt',text)
if __name__=='__main__':unittest.main()

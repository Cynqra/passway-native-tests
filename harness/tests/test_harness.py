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
if __name__=='__main__':unittest.main()

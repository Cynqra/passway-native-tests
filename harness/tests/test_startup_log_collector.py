import ast
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

from startup_log_collector import StartupLogCollector, parse_marker_line


class FakeStream:
    def __init__(self, lines, close_event, *, early_exit=False, hang_on_read=False, unblock_hang=None, started_reading=None):
        self._buffer = io.StringIO(''.join(lines))
        self._close_event = close_event
        self._early_exit = early_exit
        self._hang_on_read = hang_on_read
        self._unblock_hang = unblock_hang
        self._started_reading = started_reading
        self.drained = threading.Event()
        self.closed = False

    def readline(self, size=-1):
        if self._hang_on_read:
            if self._started_reading is not None:
                self._started_reading.set()
            if self._unblock_hang is not None:
                self._unblock_hang.wait(timeout=2.0)
        chunk = self._buffer.readline(size)
        if chunk:
            return chunk
        self.drained.set()
        if not self._early_exit:
            self._close_event.wait(timeout=2.0)
        return ''

    def close(self):
        self.closed = True
        self._close_event.set()


class FakeProcess:
    def __init__(
        self,
        lines,
        *,
        stubborn=False,
        unstoppable=False,
        early_exit=False,
        hang_on_read=False,
        unblock_hang=None,
        started_reading=None,
    ):
        self._close_event = threading.Event()
        self.stdout = FakeStream(
            lines,
            self._close_event,
            early_exit=early_exit,
            hang_on_read=hang_on_read,
            unblock_hang=unblock_hang,
            started_reading=started_reading,
        )
        self.stubborn = stubborn
        self.unstoppable = unstoppable
        self.terminated = False
        self.killed = False
        self.wait_calls = 0
        self._exited = early_exit

    @property
    def drained(self):
        return self.stdout.drained

    def poll(self):
        return 0 if self._exited else None

    def terminate(self):
        self.terminated = True
        if not self.stubborn and not self.unstoppable:
            self._exited = True
            self._close_event.set()

    def kill(self):
        self.killed = True
        if not self.unstoppable:
            self._exited = True
            self._close_event.set()

    def wait(self, timeout=None):
        self.wait_calls += 1
        if self.unstoppable:
            raise subprocess.TimeoutExpired(cmd=['adb', 'logcat'], timeout=timeout or 0)
        if self.stubborn and not self.killed:
            raise subprocess.TimeoutExpired(cmd=['adb', 'logcat'], timeout=timeout or 0)
        self._exited = True
        self._close_event.set()
        return 0


class TestStartupLogCollector(unittest.TestCase):
    def test_parse_marker_whitelist_and_privacy_rejection(self):
        self.assertEqual(
            parse_marker_line('[startup-phase] auth_wait\n'),
            ('startup-phase', 'auth_wait'),
        )
        self.assertEqual(
            parse_marker_line('10-17 07:58:00.123  1234  5678 I ReactNativeJS: [startup-phase] ensure_user_doc\r\n'),
            ('startup-phase', 'ensure_user_doc'),
        )
        self.assertEqual(
            parse_marker_line('10-17 07:58:20.123  1234  5678 W ReactNativeJS: [startup-watchdog] find_active_connection'),
            ('startup-watchdog', 'find_active_connection'),
        )

        self.assertIsNone(parse_marker_line('10-17 07:58:00.123  1234  5678 I ReactNativeJS: [startup-phase] auth_wait uid=secret'))
        self.assertIsNone(parse_marker_line('10-17 07:58:00.123  1234  5678 I ReactNativeJS: Chat: [startup-phase] complete'))
        self.assertIsNone(parse_marker_line('10-17 07:58:00.123  1234  5678 I ReactNativeJS: prefix [startup-phase] complete'))
        self.assertIsNone(parse_marker_line('[startup-phase] unknown_phase'))
        self.assertIsNone(parse_marker_line('[custom-marker] auth_wait'))
        self.assertIsNone(parse_marker_line('[startup-phase] auth_wait\n[startup-phase] complete'))

    def test_stream_capture_filters_pii_and_writes_jsonl(self):
        lines = [
            '10-17 07:58:00.010  1000  1001 I Auth: user=alice-uid phone=+15550001111 token=eyJsecret\n',
            '10-17 07:58:00.100  1000  1001 I ReactNativeJS: [startup-phase] auth_wait\n',
            '10-17 07:58:00.200  1000  1001 I ReactNativeJS: [startup-phase] auth_wait extra-secret\n',
            '10-17 07:58:00.300  1000  1001 I ReactNativeJS: [startup-phase] ensure_user_doc\n',
            '10-17 07:58:20.100  1000  1001 W ReactNativeJS: [startup-watchdog] ensure_user_doc\n',
        ]
        clock = [100.0]
        def fake_monotonic():
            clock[0] += 0.5
            return clock[0]

        proc_holder = []
        def fake_popen(cmd, **kwargs):
            self.assertEqual(cmd, ['adb', 'logcat', '-v', 'threadtime'])
            self.assertFalse(kwargs.get('shell', True))
            proc = FakeProcess(lines)
            proc_holder.append(proc)
            return proc

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'startup-phases.jsonl'
            with StartupLogCollector(out, started=100.0, popen_fn=fake_popen, monotonic_fn=fake_monotonic) as collector:
                self.assertTrue(proc_holder[0].drained.wait(timeout=2.0))

            raw = out.read_text('utf-8')
            self.assertNotIn('alice-uid', raw)
            self.assertNotIn('+15550001111', raw)
            self.assertNotIn('eyJsecret', raw)
            self.assertNotIn('extra-secret', raw)

            records = [json.loads(line) for line in raw.splitlines()]
            self.assertEqual(len(records), 3)
            self.assertEqual([(r['event'], r['phase']) for r in records], [
                ('startup-phase', 'auth_wait'),
                ('startup-phase', 'ensure_user_doc'),
                ('startup-watchdog', 'ensure_user_doc'),
            ])
            for r in records:
                self.assertEqual(set(r.keys()), {'elapsed_seconds', 'event', 'phase'})

            summary = collector.summary()
            self.assertEqual(summary, {
                'status': 'captured',
                'events_recorded': 3,
                'last_phase': 'ensure_user_doc',
                'last_watchdog': 'ensure_user_doc',
                'truncated': False,
            })
            self.assertTrue(proc_holder[0].terminated)
            self.assertFalse(proc_holder[0].killed)
            self.assertGreaterEqual(proc_holder[0].wait_calls, 1)

    def test_no_marker_stream_reports_diagnostic_limitation(self):
        proc = FakeProcess([
            '10-17 07:58:00.010  1000  1001 I ActivityManager: Displayed MainActivity\n',
            '10-17 07:58:01.000  1000  1001 I ReactNativeJS: Running main\n',
        ])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'startup-phases.jsonl'
            with StartupLogCollector(out, started=0.0, popen_fn=lambda *a, **kw: proc) as collector:
                self.assertTrue(proc.drained.wait(timeout=2.0))

            self.assertEqual(out.read_text('utf-8'), '')
            self.assertEqual(collector.summary(), {
                'status': 'diagnostic_limitation',
                'events_recorded': 0,
                'last_phase': None,
                'last_watchdog': None,
                'truncated': False,
                'limitation': 'no_startup_markers_captured',
            })

    def test_early_exit_reports_diagnostic_limitation(self):
        empty_early = FakeProcess([], early_exit=True)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'startup-phases.jsonl'
            with StartupLogCollector(out, started=0.0, popen_fn=lambda *a, **kw: empty_early) as collector:
                self.assertTrue(empty_early.drained.wait(timeout=2.0))
                collector._thread.join(timeout=2.0)

            self.assertEqual(empty_early.wait_calls, 1)
            self.assertEqual(collector.summary(), {
                'status': 'diagnostic_limitation',
                'events_recorded': 0,
                'last_phase': None,
                'last_watchdog': None,
                'truncated': False,
                'limitation': 'logcat_exited_early',
            })

        partial_early = FakeProcess(['[startup-phase] auth_wait\n'], early_exit=True)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'startup-phases.jsonl'
            with StartupLogCollector(out, started=0.0, popen_fn=lambda *a, **kw: partial_early) as collector:
                self.assertTrue(partial_early.drained.wait(timeout=2.0))
                collector._thread.join(timeout=2.0)

            self.assertEqual(collector.summary(), {
                'status': 'diagnostic_limitation',
                'events_recorded': 1,
                'last_phase': 'auth_wait',
                'last_watchdog': None,
                'truncated': False,
                'limitation': 'logcat_exited_early',
            })

    def test_immediate_stop_without_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'startup-phases.jsonl'
            for _ in range(10):
                proc = FakeProcess(['[startup-phase] auth_wait\n'])
                with StartupLogCollector(out, started=0.0, popen_fn=lambda *a, **kw: proc) as collector:
                    pass
                self.assertTrue(proc.terminated)
                self.assertGreaterEqual(proc.wait_calls, 1)
                self.assertIn(collector.summary()['status'], {'captured', 'diagnostic_limitation'})

    def test_bounds_max_events_and_oversized_line_discard(self):
        oversized = 'X' * 200 + '\n'
        lines = [
            oversized,
            '[startup-phase] auth_wait\n',
            '[startup-phase] ensure_user_doc\n',
            '[startup-phase] find_active_connection\n',
            '[startup-phase] complete\n',
        ]
        proc = FakeProcess(lines)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'startup-phases.jsonl'
            with StartupLogCollector(
                out,
                started=10.0,
                popen_fn=lambda *a, **kw: proc,
                monotonic_fn=lambda: 11.0,
                max_events=2,
                max_line_bytes=64,
            ) as collector:
                self.assertTrue(proc.drained.wait(timeout=2.0))

            records = [json.loads(line) for line in out.read_text('utf-8').splitlines()]
            self.assertEqual(len(records), 2)
            self.assertEqual([r['phase'] for r in records], ['auth_wait', 'ensure_user_doc'])
            summary = collector.summary()
            self.assertEqual(summary['status'], 'truncated')
            self.assertTrue(summary['truncated'])
            self.assertEqual(summary['events_recorded'], 2)

    def test_stubborn_process_escalates_terminate_to_kill(self):
        proc = FakeProcess(['[startup-phase] auth_wait\n'], stubborn=True)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'startup-phases.jsonl'
            with StartupLogCollector(
                out,
                started=0.0,
                popen_fn=lambda *a, **kw: proc,
                terminate_timeout=0.05,
            ) as collector:
                self.assertTrue(proc.drained.wait(timeout=2.0))

            self.assertTrue(proc.terminated)
            self.assertTrue(proc.killed)
            self.assertGreaterEqual(proc.wait_calls, 2)
            self.assertEqual(collector.summary()['status'], 'captured')

    def test_cleanup_failures_report_diagnostic_limitation(self):
        unstoppable = FakeProcess(['[startup-phase] auth_wait\n'], unstoppable=True)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'startup-phases.jsonl'
            with StartupLogCollector(
                out,
                started=0.0,
                popen_fn=lambda *a, **kw: unstoppable,
                terminate_timeout=0.02,
            ) as collector:
                self.assertTrue(unstoppable.drained.wait(timeout=2.0))
            unstoppable._close_event.set()

            self.assertTrue(unstoppable.terminated)
            self.assertTrue(unstoppable.killed)
            self.assertEqual(collector.summary(), {
                'status': 'diagnostic_limitation',
                'events_recorded': 1,
                'last_phase': 'auth_wait',
                'last_watchdog': None,
                'truncated': False,
                'limitation': 'logcat_cleanup_incomplete',
            })

        unblock = threading.Event()
        started_reading = threading.Event()
        hanging = FakeProcess(
            ['[startup-phase] auth_wait\n'],
            hang_on_read=True,
            unblock_hang=unblock,
            started_reading=started_reading,
        )
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / 'startup-phases.jsonl'
                collector = StartupLogCollector(
                    out,
                    started=0.0,
                    popen_fn=lambda *a, **kw: hanging,
                    terminate_timeout=0.02,
                )
                collector.start()
                self.assertTrue(started_reading.wait(timeout=2.0))
                collector.stop()
                self.assertEqual(collector.summary()['status'], 'diagnostic_limitation')
                self.assertEqual(collector.summary()['limitation'], 'logcat_cleanup_incomplete')
        finally:
            unblock.set()

    def test_spawn_failure_reports_limitation_without_leaking_error_details(self):
        def failing_popen(*args, **kwargs):
            raise OSError('adb failed for secret-user-token-999')

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'startup-phases.jsonl'
            with StartupLogCollector(out, started=0.0, popen_fn=failing_popen) as collector:
                pass

            self.assertEqual(out.read_text('utf-8'), '')
            summary = collector.summary()
            self.assertEqual(summary, {
                'status': 'diagnostic_limitation',
                'events_recorded': 0,
                'last_phase': None,
                'last_watchdog': None,
                'truncated': False,
                'limitation': 'logcat_collector_unavailable',
            })
            self.assertNotIn('secret-user-token-999', json.dumps(summary))

    def test_coordinator_integration_cleans_up_on_timeout(self):
        coord_path = HARNESS_DIR / 'isolated_coordinator.py'
        tree = ast.parse(coord_path.read_text('utf-8'))
        main_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        mod = ast.Module(body=[main_node], type_ignores=[])
        ast.fix_missing_locations(mod)
        code_obj = compile(mod, filename=str(coord_path), mode='exec')

        proc = FakeProcess(['[startup-phase] auth_wait\n', '[startup-watchdog] auth_wait\n'])
        published = []

        class FakeSubprocess:
            TimeoutExpired = subprocess.TimeoutExpired
            @staticmethod
            def run(cmd, timeout=None):
                proc.drained.wait(timeout=2.0)
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'startup-phases.jsonl').write_text('stale\n', encoding='utf-8')

            def collector_factory(output_path, *, started=None):
                return StartupLogCollector(output_path, started=started, popen_fn=lambda *a, **kw: proc)

            env = {
                'json': json,
                'os': os,
                'pathlib': Path,
                'subprocess': FakeSubprocess,
                'sys': sys,
                'time': time,
                'StartupLogCollector': collector_factory,
                'publish': lambda state, **kw: published.append((state, kw)),
                'ROOT': root,
            }
            exec(code_obj, env)
            rc = env['main']()

            self.assertEqual(rc, 124)
            self.assertTrue(proc.terminated)
            result = json.loads((root / 'coordinator-result.json').read_text('utf-8'))
            self.assertEqual(result['exit_code'], 124)
            self.assertFalse(result['passed'])
            self.assertEqual(result['startup_diagnostics']['status'], 'captured')
            self.assertEqual(result['startup_diagnostics']['last_watchdog'], 'auth_wait')

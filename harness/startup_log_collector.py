"""Privacy-safe bounded adb logcat collector for fixed startup phase markers."""
import json
import pathlib
import re
import subprocess
import threading
import time

WHITELISTED_EVENTS = frozenset({
    'startup-phase',
    'startup-watchdog',
})

WHITELISTED_PHASES = frozenset({
    'auth_wait',
    'welcome_check',
    'ensure_user_doc',
    'find_active_connection',
    'complete',
    'load_error',
    'auth_error',
})

_MARKER_RE = re.compile(
    r'^(?:\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+[VDIWEFA]\s+[^:\r\n]+:\s*)?'
    r'\[(startup-phase|startup-watchdog)\] '
    r'(auth_wait|welcome_check|ensure_user_doc|find_active_connection|complete|load_error|auth_error)$'
)

DEFAULT_MAX_EVENTS = 256
DEFAULT_MAX_LINE_BYTES = 4096


def parse_marker_line(line: str):
    """Return (event, phase) if line is an exact whitelisted marker, else None."""
    if not isinstance(line, str):
        return None
    cleaned = line.rstrip('\r\n')
    if '\n' in cleaned or '\r' in cleaned:
        return None
    match = _MARKER_RE.fullmatch(cleaned)
    if not match:
        return None
    event, phase = match.group(1), match.group(2)
    if event not in WHITELISTED_EVENTS or phase not in WHITELISTED_PHASES:
        return None
    return event, phase


class StartupLogCollector:
    def __init__(
        self,
        output_path,
        *,
        started=None,
        cmd=None,
        popen_fn=subprocess.Popen,
        monotonic_fn=time.monotonic,
        max_events=DEFAULT_MAX_EVENTS,
        max_line_bytes=DEFAULT_MAX_LINE_BYTES,
        terminate_timeout=2.0,
    ):
        self.output_path = pathlib.Path(output_path)
        self._monotonic = monotonic_fn
        self._started = self._monotonic() if started is None else started
        self._cmd = list(cmd) if cmd is not None else ['adb', 'logcat', '-v', 'threadtime']
        self._popen = popen_fn
        self._max_events = max(1, int(max_events))
        self._max_line_bytes = max(64, int(max_line_bytes))
        self._terminate_timeout = float(terminate_timeout)

        self._proc = None
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        self.events_recorded = 0
        self.last_phase = None
        self.last_watchdog = None
        self.truncated = False
        self.limitation = None

    def start(self):
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            self.output_path.write_text('', encoding='utf-8')
            self._proc = self._popen(
                self._cmd,
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding='utf-8',
                errors='replace',
            )
        except Exception:
            self._proc = None
            self.limitation = 'logcat_collector_unavailable'
            return self

        stream = self._proc.stdout
        if stream is None:
            self.limitation = 'logcat_collector_unavailable'
            self._cleanup_process()
            return self

        self._thread = threading.Thread(
            target=self._consume_stream,
            args=(stream,),
            name='startup-log-collector',
            daemon=True,
        )
        self._thread.start()
        return self

    def _consume_stream(self, stream):
        discard_until_newline = False
        try:
            with self.output_path.open('a', encoding='utf-8') as out_file:
                while not self._stop_event.is_set():
                    chunk = stream.readline(self._max_line_bytes)
                    if not chunk:
                        if not self._stop_event.is_set():
                            with self._lock:
                                if self.limitation is None:
                                    self.limitation = 'logcat_exited_early'
                        break
                    has_newline = chunk.endswith('\n') or chunk.endswith('\r')
                    if discard_until_newline:
                        if has_newline:
                            discard_until_newline = False
                        continue
                    if not has_newline and len(chunk) >= self._max_line_bytes:
                        discard_until_newline = True
                        continue
                    parsed = parse_marker_line(chunk)
                    if parsed is None:
                        continue
                    event, phase = parsed
                    elapsed = round(max(0.0, self._monotonic() - self._started), 3)
                    with self._lock:
                        if self.events_recorded >= self._max_events:
                            self.truncated = True
                            continue
                        self.events_recorded += 1
                        if event == 'startup-phase':
                            self.last_phase = phase
                        elif event == 'startup-watchdog':
                            self.last_watchdog = phase
                        record = {
                            'elapsed_seconds': elapsed,
                            'event': event,
                            'phase': phase,
                        }
                        out_file.write(json.dumps(record, separators=(',', ':')) + '\n')
                        out_file.flush()
        except Exception:
            if not self._stop_event.is_set():
                with self._lock:
                    if self.limitation is None:
                        self.limitation = 'logcat_stream_interrupted'

    def _cleanup_process(self):
        proc = self._proc
        self._proc = None
        if proc is None:
            return
        cleanup_failed = False
        try:
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    cleanup_failed = True
                try:
                    proc.wait(timeout=self._terminate_timeout)
                except subprocess.TimeoutExpired:
                    try:
                        proc.kill()
                    except Exception:
                        cleanup_failed = True
                    try:
                        proc.wait(timeout=self._terminate_timeout)
                    except Exception:
                        cleanup_failed = True
                except Exception:
                    cleanup_failed = True
            else:
                try:
                    proc.wait(timeout=self._terminate_timeout)
                except Exception:
                    cleanup_failed = True
            if proc.poll() is None:
                cleanup_failed = True
        finally:
            if proc.stdout is not None:
                try:
                    proc.stdout.close()
                except Exception:
                    pass
            if cleanup_failed:
                with self._lock:
                    self.limitation = 'logcat_cleanup_incomplete'

    def stop(self):
        self._stop_event.set()
        self._cleanup_process()
        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.join(timeout=self._terminate_timeout)
            if thread.is_alive():
                with self._lock:
                    self.limitation = 'logcat_cleanup_incomplete'

    def summary(self):
        with self._lock:
            limitation = self.limitation
            if limitation is None and self.events_recorded == 0:
                limitation = 'no_startup_markers_captured'
            if limitation is not None:
                status = 'diagnostic_limitation'
            elif self.truncated:
                status = 'truncated'
            else:
                status = 'captured'
            result = {
                'status': status,
                'events_recorded': self.events_recorded,
                'last_phase': self.last_phase,
                'last_watchdog': self.last_watchdog,
                'truncated': self.truncated,
            }
            if limitation is not None:
                result['limitation'] = limitation
            return result

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False

import ast
import unittest
from pathlib import Path

class TestStartupFailfast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parents[1] / 'native_isolated_e2e.py'
        source = path.read_text('utf-8')
        tree = ast.parse(source)
        
        func_node = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'ready_generate':
                func_node = node
                break
        if not func_node:
            raise RuntimeError('ready_generate not found in native_isolated_e2e.py')
        
        module_node = ast.Module(body=[func_node], type_ignores=[])
        ast.fix_missing_locations(module_node)
        cls.code_obj = compile(module_node, filename=str(path), mode='exec')

    def test_startup_error_fails_fast(self):
        sleep_called = [False]
        class MockTime:
            def __init__(self):
                self._t = 0.0
            def monotonic(self):
                self._t += 1.0
                return self._t
            def sleep(self, seconds):
                sleep_called[0] = True

        def mock_dump():
            return "ui_tree"
            
        def mock_find(test_id, t):
            if test_id == 'startup-error':
                return "found"
            return None

        env = {
            'time': MockTime(),
            'dump': mock_dump,
            'find': mock_find,
        }
        exec(self.code_obj, env)
        ready_generate = env['ready_generate']

        with self.assertRaises(RuntimeError) as ctx:
            ready_generate()
        self.assertIn('Startup failed: startup-error visible', str(ctx.exception))
        self.assertFalse(sleep_called[0], 'Should not sleep or loop when startup-error is present')

    def test_normal_wait_until_controls_appear(self):
        sleep_count = [0]
        class MockTime:
            def __init__(self):
                self._t = 0.0
            def monotonic(self):
                self._t += 5.0
                return self._t
            def sleep(self, seconds):
                sleep_count[0] += 1

        calls = [0]
        def mock_dump():
            calls[0] += 1
            return f"dump-{calls[0]}"
            
        def mock_find(test_id, t):
            if test_id == 'name-input':
                return 'found' if t == 'dump-2' else None
            if test_id == 'generate':
                return 'found' if t == 'dump-2' else None
            return None

        env = {
            'time': MockTime(),
            'dump': mock_dump,
            'find': mock_find,
        }
        exec(self.code_obj, env)
        ready_generate = env['ready_generate']

        ready_generate()
        self.assertEqual(sleep_count[0], 1)

    def test_success_returns(self):
        class MockTime:
            def monotonic(self):
                return 0.0
            def sleep(self, seconds):
                pass

        def mock_dump():
            return "ui_tree"
            
        def mock_find(test_id, t):
            if test_id in ('name-input', 'generate'):
                return "found"
            return None

        env = {
            'time': MockTime(),
            'dump': mock_dump,
            'find': mock_find,
        }
        exec(self.code_obj, env)
        ready_generate = env['ready_generate']

        ready_generate()

    def test_timeout_raises_generate_not_reached(self):
        class MockTime:
            def __init__(self):
                self._t = 0.0
            def monotonic(self):
                self._t += 101.0
                return self._t
            def sleep(self, seconds):
                pass

        def mock_dump():
            return "ui_tree"
            
        def mock_find(test_id, t):
            return None

        env = {
            'time': MockTime(),
            'dump': mock_dump,
            'find': mock_find,
        }
        exec(self.code_obj, env)
        ready_generate = env['ready_generate']

        with self.assertRaises(RuntimeError) as ctx:
            ready_generate()
        self.assertEqual('Generate form not reached', str(ctx.exception))

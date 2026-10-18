import ast
import unittest
import json
import re
from pathlib import Path

class Sentinel(Exception):
    pass

class TestAccessibilityConfigCycles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parents[1] / 'native_accessibility_journey.py'
        source = path.read_text('utf-8')
        tree = ast.parse(source)

        func_node = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'run':
                func_node = node
                break
        if not func_node:
            raise RuntimeError('run function not found in native_accessibility_journey.py')

        module_node = ast.Module(body=[func_node], type_ignores=[])
        ast.fix_missing_locations(module_node)
        cls.code_obj = compile(module_node, filename=str(path), mode='exec')

    def test_config_cycles_sentinel_and_finally(self):
        shell_calls = []
        ready_calls = []
        user_calls = []
        records = []

        def mock_shell(*args):
            shell_calls.append(list(args))
            if args[0] == 'settings' and len(args) > 3 and args[3] == 'get':
                uid = int(args[2])
                return '1.25' if uid == 0 else '1.5'
            if args[:2] == ('wm', 'size') and len(args) == 2:
                return 'Override size: 440x880'
            return ''

        def mock_user(uid):
            user_calls.append(uid)

        def mock_ready():
            ready_calls.append(True)
            if len(ready_calls) == 3:
                raise Sentinel()

        env = {
            'shell': mock_shell,
            'ROOT': Path('.'),
            'json': json,
            're': re,
            'fill': lambda *a: None,
            'tap': lambda *a: None,
            'tapnode': lambda *a: None,
            'waitfor': lambda *a: None,
            'find': lambda *a: None,
            'dump': lambda *a: None,
            'swipe_viewport': lambda *a: None,
            'record': lambda msg, status, detail: records.append((msg, status, detail)),
        }

        ctx = {
            'user': mock_user,
            'ready_generate': mock_ready,
            'hide_keyboard': lambda: None,
            'snap': lambda *a: None,
            'check': lambda msg, cond: None,
        }

        exec(self.code_obj, env)
        run = env['run']

        with self.assertRaises(Sentinel):
            run(ctx, 10)

        # Verify exactly 3 ready and user(0) calls
        self.assertEqual(len(ready_calls), 3)
        self.assertEqual(user_calls.count(0), 3)

        self.assertEqual(shell_calls[-3:], [
            ['wm', 'size', 'reset'],
            ['settings', '--user', 0, 'put', 'system', 'font_scale', '1.25'],
            ['settings', '--user', 10, 'put', 'system', 'font_scale', '1.5']
        ])

        self.assertEqual(records, [('Configuration cycle 1 completed', 'PASS', 'Cycle validated')])

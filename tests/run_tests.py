#!/usr/bin/env python3
"""Minimal test runner — no pytest required."""
import sys, os, asyncio, tempfile, time, json, traceback, importlib, inspect, types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Shim pytest so the test file can import it
pytest_shim = types.ModuleType('pytest')
sys.modules['pytest'] = pytest_shim

sys.path.insert(0, str(Path(__file__).parent.parent))

def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)

passed = failed = 0
failures = []

spec = importlib.util.spec_from_file_location('test_phase', str(Path(__file__).parent / 'test_phase.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

test_classes = []
for name in dir(mod):
    obj = getattr(mod, name)
    if isinstance(obj, type) and name.startswith('Test'):
        test_classes.append(obj)

test_classes.sort(key=lambda c: c.__name__)

for cls in test_classes:
    inst = cls()
    methods = [m for m in dir(inst) if m.startswith('test_')]
    for method_name in sorted(methods):
        method = getattr(inst, method_name)
        sig = inspect.signature(method)
        try:
            if 'tmp_path' in sig.parameters:
                with tempfile.TemporaryDirectory() as td:
                    method(Path(td))
            else:
                method()
            passed += 1
            print(f'  PASS: {cls.__name__}.{method_name}')
        except Exception as exc:
            failed += 1
            tb = traceback.format_exc()
            failures.append((f'{cls.__name__}.{method_name}', tb))
            print(f'  FAIL: {cls.__name__}.{method_name}: {exc}')

print(f'\n{"="*60}')
print(f'RESULTS: {passed} passed, {failed} failed, {passed+failed} total')
if failures:
    print(f'\nFAILURES:')
    for name, tb in failures:
        print(f'\n--- {name} ---')
        print(tb[-800:])
    sys.exit(1)

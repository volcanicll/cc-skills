# -*- coding: utf-8 -*-
"""运行全部测试：python3 tests/run_all.py"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = ["test_yamlio.py", "test_xlsx.py", "test_net.py", "test_ws.py",
         "test_state_api.py", "test_config.py", "test_auth.py", "test_export.py", "test_cli.py"]

ok = True
for t in TESTS:
    path = os.path.join(HERE, t)
    print(f"===== {t} =====")
    r = subprocess.run([sys.executable, path], cwd=os.path.dirname(HERE))
    if r.returncode != 0:
        ok = False
        print(f"  ❌ {t} failed")
if not ok:
    sys.exit(1)
print("ALL TESTS PASSED")

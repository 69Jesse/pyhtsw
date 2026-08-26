import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

result = subprocess.run(
    [sys.executable, str(ROOT / 'scripts' / 'gen_types.py'), '--check'],
    capture_output=True,
    text=True,
    check=False,
)
assert result.returncode == 0, result.stdout + result.stderr

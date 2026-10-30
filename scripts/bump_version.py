"""Bump the service-worker cache version (docs/sw.js). Run before every deploy so phones fetch the new shell."""
import re
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "docs" / "sw.js"
s = p.read_text(encoding="utf-8")
new = int(re.search(r'const VERSION = "(\d+)"', s).group(1)) + 1
p.write_text(re.sub(r'const VERSION = "\d+"', f'const VERSION = "{new}"', s), encoding="utf-8")
print("sw.js cache version ->", new)

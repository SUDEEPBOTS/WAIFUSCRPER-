"""
WAIFUSCRPER — tools/__init__.py
Auto-discovers all plugin modules inside the tools/ folder.
"""

import os
from pathlib import Path

# Build list of all importable modules inside tools/
# e.g.  tools/start.py        → ".start"
#        tools/Sudo/Sudo.py    → ".Sudo.Sudo"
#        tools/dwonloder/...   → ".dwonloder.Dwonlod"

_tools_dir = Path(__file__).parent
ALL_MODULES: list[str] = []

for _path in sorted(_tools_dir.rglob("*.py")):
    # Skip __init__ files
    if _path.name == "__init__.py":
        continue

    # Build dotted relative path  e.g. "Sudo/Sudo.py" → ".Sudo.Sudo"
    _rel   = _path.relative_to(_tools_dir)
    _parts = list(_rel.with_suffix("").parts)
    ALL_MODULES.append("." + ".".join(_parts))
  

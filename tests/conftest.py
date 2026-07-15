from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# 防止分析模块导入时尝试打开图形界面。
os.environ.setdefault("MPLBACKEND", "Agg")

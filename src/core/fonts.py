from __future__ import annotations

import sys
from pathlib import Path


def find_dejavu_sans(*, bold: bool = False) -> str | None:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu") / name,
        Path(sys.prefix) / "share" / "fonts" / "TTF" / name,
        Path("/data/data/com.termux/files/usr/share/fonts/TTF") / name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None

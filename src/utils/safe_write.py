# src/utils/safe_write.py
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path


def atomic_write_text(final_path: Path, content: str, encoding: str = "utf-8") -> Path:
    """
    Two-phase commit for text files:
      1) write to sibling temp file (.tmp)
      2) fsync to disk
      3) backup existing final file (.bak) best-effort
      4) atomic replace (os.replace)
    """
    final_path = final_path.resolve()
    final_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")
    bak_path = final_path.with_suffix(final_path.suffix + ".bak")

    # 1) Write temp
    with open(tmp_path, "w", encoding=encoding, newline="\n") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())

    # 2) Backup existing final (best-effort)
    if final_path.exists():
        try:
            shutil.copy2(final_path, bak_path)
        except Exception:
            pass

    # 3) Atomic replace
    os.replace(tmp_path, final_path)

    # 4) Marker (best-effort)
    try:
        (final_path.parent / ".last_write").write_text(str(time.time()), encoding="utf-8")
    except Exception:
        pass

    return final_path
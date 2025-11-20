from pathlib import Path
import shutil

# backend/app/utils/pyfile_ops.py

def safe_write(path: Path, content: str, mode: str = "w"):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, mode, encoding="utf-8") as f:
        f.write(content)
    shutil.move(str(tmp), str(path))

def read_file(path: Path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

def safe_copy(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)


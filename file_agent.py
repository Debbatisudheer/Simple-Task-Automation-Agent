import os
import shutil
from pathlib import Path

CATEGORIES = {
    "Images":      {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".heic", ".svg"},
    "Videos":      {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"},
    "Audio":       {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"},
    "Archives":    {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Documents":   {".txt", ".rtf", ".md"},
    "PDFs":        {".pdf"},
    "Spreadsheets":{".xls", ".xlsx", ".csv", ".ods"},
    "Presentations":{".ppt", ".pptx", ".odp"},
    "Code":        {".py", ".js", ".ts", ".java", ".go", ".cs", ".cpp", ".c", ".rs", ".rb", ".php", ".sh", ".bat", ".ps1"},
    "Executables": {".exe", ".msi", ".apk", ".dmg"},
    "Design":      {".psd", ".ai", ".fig", ".xd", ".sketch"},
}

def _category_for(ext: str) -> str:
    ext = ext.lower()
    for cat, exts in CATEGORIES.items():
        if ext in exts:
            return cat
    return "Others"

def _unique_destination(dst_dir: Path, filename: str) -> Path:
    base = Path(filename).stem
    ext = Path(filename).suffix
    candidate = dst_dir / (base + ext)
    counter = 1
    while candidate.exists():
        candidate = dst_dir / f"{base} ({counter}){ext}"
        counter += 1
    return candidate

def organize_files(root: str, dry_run: bool = False) -> None:
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists() or not root_path.is_dir():
        print(f"❌ Path not found or not a folder: {root_path}")
        return

    print(f"{'🧪 DRY RUN' if dry_run else '🗂️  Organizing'} in: {root_path}")
    moved, skipped = 0, 0

    for item in root_path.iterdir():
        if item.is_dir():
            # Skip top-level folders we create
            if item.name in set(CATEGORIES.keys()) | {"Others"}:
                continue
            # Skip existing folders; we only move top-level files in v1
            skipped += 1
            continue

        if item.is_file():
            cat = _category_for(item.suffix)
            target_dir = root_path / cat
            if not dry_run:
                target_dir.mkdir(exist_ok=True)
                dst = _unique_destination(target_dir, item.name)
                try:
                    shutil.move(str(item), str(dst))
                    print(f"➡️  {item.name}  →  {cat}/{dst.name}")
                    moved += 1
                except Exception as e:
                    print(f"❌ Failed to move {item.name}: {e}")
                    skipped += 1
            else:
                print(f"🧪 Would move: {item.name} → {cat}/")
                moved += 1

    print(f"\n✅ Done. {'Simulated' if dry_run else 'Moved'}: {moved}, Skipped: {skipped}")

import os
import zipfile

base_dir = r"c:\Users\Nishant\Downloads\ai_smartrail"
zip_path = os.path.join(base_dir, "ai_smartrail_complete.zip")

exclude_dirs = {".git", "__pycache__", ".pytest_cache", ".vscode"}
exclude_exts = {".pyc", ".log", ".tmp"}

print("Packaging project zip...")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if f == "ai_smartrail_complete.zip":
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in exclude_exts:
                continue
            full_path = os.path.join(root, f)
            arcname = os.path.relpath(full_path, base_dir)
            zf.write(full_path, arcname)

size = os.path.getsize(zip_path)
print(f"✓ Created {zip_path} ({size:,} bytes)")

import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUDE = ["analyzer.py", "config.json", "README.md", "LICENSE", "run.bat", "run.sh", "modules", "runtime"]
SKIP_FOLDERS = {"__pycache__"}


def add_path(archive, relative_path, root_name):
    full_path = os.path.join(ROOT, relative_path)
    if os.path.isfile(full_path):
        archive.write(full_path, os.path.join(root_name, relative_path))
        return
    for current, folders, names in os.walk(full_path):
        folders[:] = [folder for folder in folders if folder not in SKIP_FOLDERS]
        for name in names:
            path = os.path.join(current, name)
            archive.write(path, os.path.join(root_name, os.path.relpath(path, ROOT)))


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/build_release.py <version>")
        return

    version = sys.argv[1]
    root_name = f"AssetsAnalyzer-{version}"
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    zip_path = os.path.join(ROOT, "dist", root_name + ".zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for relative_path in INCLUDE:
            if os.path.exists(os.path.join(ROOT, relative_path)):
                add_path(archive, relative_path, root_name)
            else:
                print(f"Skipped (not found): {relative_path}")

    print(f"Created: {zip_path}")


if __name__ == "__main__":
    main()
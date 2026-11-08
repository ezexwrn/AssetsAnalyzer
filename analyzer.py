import os
import sys

from modules import inventory


def format_size(total_bytes):
    value = float(total_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <game_folder>")
        return

    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"Folder not found: {folder}")
        return

    files = inventory.scan(folder)
    total = sum(f["size"] for f in files)

    print(f"\nAnalyzing: {folder}")
    print(f"Files: {len(files)} | Total size: {format_size(total)}\n")

    print("== By category ==")
    summary = inventory.summary_by_category(files)
    for category, data in sorted(summary.items(), key=lambda x: x[1]["size"], reverse=True):
        percentage = data["size"] / total * 100 if total else 0
        print(f"{category:12} {data['count']:6} files  {format_size(data['size']):>10}  ({percentage:.1f}%)")

    print("\n== By top-level folder ==")
    folders = inventory.summary_by_folder(files)
    for folder, data in sorted(folders.items(), key=lambda x: x[1]["size"], reverse=True)[:15]:
        print(f"{folder:30} {data['count']:6} files  {format_size(data['size']):>10}")

    print("\n== Extensions in 'other' ==")
    other = inventory.summary_by_extension(files, "other")
    for extension, data in sorted(other.items(), key=lambda x: x[1]["size"], reverse=True)[:15]:
        print(f"{extension or '(none)':12} {data['count']:6} files  {format_size(data['size']):>10}")

    print("\n== Top 20 heaviest ==")
    for file in inventory.heaviest(files):
        print(f"{format_size(file['size']):>10}  {file['path']}")


if __name__ == "__main__":
    main()
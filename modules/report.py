import json
import os
from datetime import datetime
from html import escape

from modules import inventory

TOP_EXTENSIONS = 15


def format_size(total_bytes):
    value = float(total_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024


def _format_difference(difference):
    sign = "-" if difference < 0 else "+"
    return f"{sign}{format_size(abs(difference))}"


def _percentage(part, total):
    return part / total * 100 if total else 0


def _sorted_by_size(summary):
    return sorted(summary.items(), key=lambda item: item[1]["size"], reverse=True)


def build(folder, files, top_files):
    return {
        "game": os.path.basename(os.path.abspath(folder)),
        "folder": os.path.abspath(folder),
        "date": datetime.now().isoformat(timespec="seconds"),
        "total_files": len(files),
        "total_size": sum(f["size"] for f in files),
        "categories": inventory.summary_by_category(files),
        "folders": inventory.summary_by_folder(files),
        "extensions_other": inventory.summary_by_extension(files, "other"),
        "heaviest": inventory.heaviest(files, top_files),
    }


def print_console(data, top_folders):
    total = data["total_size"]
    print(f"\nAnalyzing: {data['folder']}")
    print(f"Files: {data['total_files']} | Total size: {format_size(total)}\n")

    print("== By category ==")
    for name, item in _sorted_by_size(data["categories"]):
        print(f"{name:12} {item['count']:6} files  {format_size(item['size']):>10}  ({_percentage(item['size'], total):.1f}%)")

    print("\n== By top-level folder ==")
    for name, item in _sorted_by_size(data["folders"])[:top_folders]:
        print(f"{name:30} {item['count']:6} files  {format_size(item['size']):>10}")

    print("\n== Extensions in 'other' ==")
    for extension, item in _sorted_by_size(data["extensions_other"])[:TOP_EXTENSIONS]:
        print(f"{extension or '(none)':12} {item['count']:6} files  {format_size(item['size']):>10}")

    print("\n== Heaviest files ==")
    for file in data["heaviest"]:
        print(f"{format_size(file['size']):>10}  {file['path']}")


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=False)


def load_json(path):
    with open(path, encoding="utf-8") as json_file:
        return json.load(json_file)


def _table(headers, rows):
    head = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f"<table><tr>{head}</tr>{body}</table>"


def save_html(data, path, top_folders):
    total = data["total_size"]
    categories = [
        (name, item["count"], format_size(item["size"]), f"{_percentage(item['size'], total):.1f}%")
        for name, item in _sorted_by_size(data["categories"])
    ]
    folders = [
        (name, item["count"], format_size(item["size"]))
        for name, item in _sorted_by_size(data["folders"])[:top_folders]
    ]
    extensions = [
        (extension or "(none)", item["count"], format_size(item["size"]))
        for extension, item in _sorted_by_size(data["extensions_other"])[:TOP_EXTENSIONS]
    ]
    heaviest = [(format_size(file["size"]), file["path"]) for file in data["heaviest"]]

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Assets Analyzer - {escape(data['game'])}</title>
<style>
body {{ font-family: sans-serif; max-width: 900px; margin: 2em auto; padding: 0 1em; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 2em; }}
th, td {{ text-align: left; padding: 4px 8px; border-bottom: 1px solid #ccc; }}
</style>
</head>
<body>
<h1>{escape(data['game'])}</h1>
<p>{escape(data['folder'])}<br>{data['total_files']} files | {format_size(total)} | {escape(data['date'])}</p>
<h2>By category</h2>
{_table(['Category', 'Files', 'Size', '%'], categories)}
<h2>By top-level folder</h2>
{_table(['Folder', 'Files', 'Size'], folders)}
<h2>Extensions in 'other'</h2>
{_table(['Extension', 'Files', 'Size'], extensions)}
<h2>Heaviest files</h2>
{_table(['Size', 'Path'], heaviest)}
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as html_file:
        html_file.write(page)


def _file_stem(data):
    name = "".join(c if c.isalnum() or c in "-_" else "_" for c in data["game"])
    stamp = data["date"].replace("-", "").replace(":", "").replace("T", "_")
    return f"{name}_{stamp}"


def save(data, reports_folder, top_folders):
    os.makedirs(reports_folder, exist_ok=True)
    base = os.path.join(reports_folder, _file_stem(data))
    json_path = base + ".json"
    html_path = base + ".html"
    save_json(data, json_path)
    save_html(data, html_path, top_folders)
    return json_path, html_path


def compare(old, new):
    names = set(old["categories"]) | set(new["categories"])
    rows = []
    for name in names:
        old_size = old["categories"].get(name, {"size": 0})["size"]
        new_size = new["categories"].get(name, {"size": 0})["size"]
        rows.append((name, old_size, new_size, new_size - old_size))
    rows.sort(key=lambda row: row[3])
    return rows


def print_comparison(old, new):
    print(f"\nOld: {old['folder']} ({old['date']})")
    print(f"New: {new['folder']} ({new['date']})\n")
    print(f"{'category':12} {'old':>10} {'new':>10} {'difference':>12}")
    for name, old_size, new_size, difference in compare(old, new):
        print(f"{name:12} {format_size(old_size):>10} {format_size(new_size):>10} {_format_difference(difference):>12}")
    total_difference = new["total_size"] - old["total_size"]
    print(f"\nTotal: {format_size(old['total_size'])} -> {format_size(new['total_size'])} ({_format_difference(total_difference)})")
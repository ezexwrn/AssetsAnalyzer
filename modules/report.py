import json
import os
from datetime import datetime
from html import escape
from modules import inventory, duplicates, signatures, executables

TOP_EXTENSIONS = 15
TOP_DUPLICATES = 10


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


def _signature_rows(data):
    rows = []
    for extension, labels in data["signatures"].items():
        total_count = sum(item["count"] for item in labels.values())
        total_size = sum(item["size"] for item in labels.values())
        top = _sorted_by_size(labels)[:5]
        detected = ", ".join(f"{label} x{item['count']}" for label, item in top)
        rows.append((total_size, extension or "(none)", total_count, detected))
    rows.sort(reverse=True)
    return [
        (extension, count, format_size(size), detected)
        for size, extension, count, detected in rows[:TOP_EXTENSIONS]
    ]


def _executable_rows(data):
    return [
        (
            item["path"],
            item["machine"],
            "dll" if item["is_dll"] else "exe",
            "yes" if item["large_address_aware"] else "no",
            format_size(item["size"]),
            "LAA candidate" if item["laa_candidate"] else "",
        )
        for item in data["executables"]
    ]


def build(folder, files, top_files, min_duplicate_size, signature_categories):
    groups = duplicates.find(files, folder, min_duplicate_size)
    return {
        "game": os.path.basename(os.path.abspath(folder)),
        "folder": os.path.abspath(folder),
        "date": datetime.now().isoformat(timespec="seconds"),
        "total_files": len(files),
        "total_size": sum(f["size"] for f in files),
        "categories": inventory.summary_by_category(files),
        "folders": inventory.summary_by_folder(files),
        "extensions_other": inventory.summary_by_extension(files, "other"),
        "signatures": signatures.summarize(files, folder, signature_categories),
        "executables": executables.summarize(files, folder),
        "duplicates": {
            "recoverable_size": duplicates.recoverable_size(groups),
            "groups": groups,
        },
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

    print("\n== Executables ==")
    for path, machine, kind, laa, size, note in _executable_rows(data):
        print(f"{machine:14} {kind:4} LAA:{laa:4} {size:>10}  {path}  {note}")

    print("\n== Detected file types ==")
    for extension, count, size, detected in _signature_rows(data):
        print(f"{extension:12} {count:6} files  {size:>10}  {detected}")

    print("\n== Duplicates ==")
    groups = data["duplicates"]["groups"]
    print(f"{len(groups)} groups | recoverable: {format_size(data['duplicates']['recoverable_size'])}")
    for group in groups[:TOP_DUPLICATES]:
        print(f"{format_size(group['size']):>10} x {len(group['paths'])}")
        shown = group["paths"][:5]
        for path in shown:
            print(f"             {path}")
        if len(group["paths"]) > len(shown):
            print(f"             ... and {len(group['paths']) - len(shown)} more")

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

    duplicate_count = len(data["duplicates"]["groups"])
    recoverable = format_size(data["duplicates"]["recoverable_size"])
    duplicate_rows = [
        (format_size(group["size"]), len(group["paths"]), ", ".join(group["paths"][:3]))
        for group in data["duplicates"]["groups"][:TOP_DUPLICATES]
    ]

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
<h2>Executables</h2>
{_table(['Path', 'Architecture', 'Type', 'LAA', 'Size', 'Note'], _executable_rows(data))}
<h2>Detected file types</h2>
{_table(['Extension', 'Files', 'Size', 'Detected types'], _signature_rows(data))}
<h2>Duplicates</h2>
<p>{duplicate_count} groups | recoverable: {recoverable}</p>
{_table(['Size each', 'Copies', 'Paths (first 3)'], duplicate_rows)}
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
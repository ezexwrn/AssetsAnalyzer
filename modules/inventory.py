import os
from collections import defaultdict

def category_of(extension, categories):
    for name, extensions in categories.items():
        if extension in extensions:
            return name
    return "other"


def scan(root_folder, categories):
    files = []
    for current_path, _, names in os.walk(root_folder):
        for name in names:
            path = os.path.join(current_path, name)
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            extension = os.path.splitext(name)[1].lower()
            files.append({
                "path": os.path.relpath(path, root_folder),
                "size": size,
                "category": category_of(extension, categories),
                "extension": extension,
            })
    return files


def summary_by_category(files):
    totals = defaultdict(lambda: {"count": 0, "size": 0})
    for file in files:
        totals[file["category"]]["count"] += 1
        totals[file["category"]]["size"] += file["size"]
    return dict(totals)


def heaviest(files, count=20):
    return sorted(files, key=lambda f: f["size"], reverse=True)[:count]

def summary_by_extension(files, category):
    totals = defaultdict(lambda: {"count": 0, "size": 0})
    for file in files:
        if file["category"] == category:
            totals[file["extension"]]["count"] += 1
            totals[file["extension"]]["size"] += file["size"]
    return dict(totals)

def summary_by_folder(files):
    totals = defaultdict(lambda: {"count": 0, "size": 0})
    for file in files:
        parts = file["path"].split(os.sep)
        folder = parts[0] if len(parts) > 1 else "(root)"
        totals[folder]["count"] += 1
        totals[folder]["size"] += file["size"]
    return dict(totals)
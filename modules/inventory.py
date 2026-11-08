import os
from collections import defaultdict

CATEGORIES = {
    "textures": {".dds", ".tga", ".png", ".jpg", ".jpeg", ".bmp", ".txd"},
    "audio": {".wav", ".mp3", ".ogg", ".flac", ".wma"},
    "video": {".bik", ".avi", ".mp4", ".wmv", ".mpg"},
    "executables": {".exe", ".dll", ".asi"},
    "config": {".ini", ".cfg", ".xml", ".json", ".txt"},
    "packed": {".img", ".pak", ".zip", ".rar", ".7z", ".cpk", ".bin"},
}


def category_of(extension):
    for name, extensions in CATEGORIES.items():
        if extension in extensions:
            return name
    return "other"


def scan(root_folder):
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
                "category": category_of(extension),
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
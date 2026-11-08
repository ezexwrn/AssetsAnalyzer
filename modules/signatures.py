import os
from collections import defaultdict

SIGNATURES = [
    ("wav", [(0, b"RIFF"), (8, b"WAVE")]),
    ("avi", [(0, b"RIFF"), (8, b"AVI ")]),
    ("riff (other)", [(0, b"RIFF")]),
    ("ogg", [(0, b"OggS")]),
    ("mp3 (ID3)", [(0, b"ID3")]),
    ("flac", [(0, b"fLaC")]),
    ("asf (wma/wmv)", [(0, bytes.fromhex("3026B2758E66CF11A6D900AA0062CE6C"))]),
    ("mp4/mov", [(4, b"ftyp")]),
    ("bink video", [(0, b"BIK")]),
    ("bink 2 video", [(0, b"KB2")]),
    ("fsb4 (fmod)", [(0, b"FSB4")]),
    ("fsb5 (fmod)", [(0, b"FSB5")]),
    ("xact wave bank", [(0, b"WBND")]),
    ("xact sound bank", [(0, b"SDBK")]),
    ("xact settings", [(0, b"XGSF")]),
    ("dds texture", [(0, b"DDS ")]),
    ("png", [(0, bytes.fromhex("89504E470D0A1A0A"))]),
    ("jpeg", [(0, bytes.fromhex("FFD8FF"))]),
    ("exe/dll (MZ)", [(0, b"MZ")]),
    ("zip", [(0, b"PK\x03\x04")]),
    ("rar", [(0, b"Rar!\x1a\x07")]),
    ("7z", [(0, bytes.fromhex("377ABCAF271C"))]),
    ("gzip", [(0, bytes.fromhex("1F8B08"))]),
    ("cab", [(0, b"MSCF")]),
    ("pdf", [(0, b"%PDF")]),
    ("rtf", [(0, b"{\\rtf")]),
    ("xml", [(0, b"<?xml")]),
    ("lua bytecode", [(0, b"\x1bLua")]),
    ("pak (PACK)", [(0, b"PACK")]),
    ("img archive (VER2)", [(0, b"VER2")]),
]

HEADER_SIZE = max(offset + len(magic) for _, conditions in SIGNATURES for offset, magic in conditions)


def detect(path):
    try:
        with open(path, "rb") as file:
            header = file.read(HEADER_SIZE)
    except OSError:
        return "unreadable"

    if not header:
        return "empty"

    for name, conditions in SIGNATURES:
        if all(header[offset:offset + len(magic)] == magic for offset, magic in conditions):
            return name

    prefix = header[:4]
    if all(32 <= byte < 127 for byte in prefix):
        return f'unknown "{prefix.decode("ascii")}"'
    return f"unknown {prefix.hex()}"


def summarize(files, root_folder, categories):
    by_extension = defaultdict(lambda: defaultdict(lambda: {"count": 0, "size": 0}))
    for file in files:
        if file["category"] not in categories:
            continue
        label = detect(os.path.join(root_folder, file["path"]))
        entry = by_extension[file["extension"]][label]
        entry["count"] += 1
        entry["size"] += file["size"]
    return {extension: dict(labels) for extension, labels in by_extension.items()}
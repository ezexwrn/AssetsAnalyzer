import hashlib
import os
from collections import defaultdict

CHUNK_SIZE = 1024 * 1024


def hash_file(path):
    digest = hashlib.sha1()
    with open(path, "rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def find(files, root_folder, min_size):
    by_size = defaultdict(list)
    for file in files:
        if file["size"] >= min_size:
            by_size[file["size"]].append(file["path"])

    groups = []
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        by_hash = defaultdict(list)
        for path in paths:
            try:
                by_hash[hash_file(os.path.join(root_folder, path))].append(path)
            except OSError:
                continue
        for same_paths in by_hash.values():
            if len(same_paths) > 1:
                groups.append({"size": size, "paths": same_paths})

    groups.sort(key=lambda group: group["size"] * (len(group["paths"]) - 1), reverse=True)
    return groups


def recoverable_size(groups):
    return sum(group["size"] * (len(group["paths"]) - 1) for group in groups)
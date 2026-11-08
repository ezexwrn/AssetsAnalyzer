import os
import struct

HEADER_SIZE = 128
DDPF_FOURCC = 0x4
PNG_COLOR_TYPES = {0: "grayscale", 2: "rgb", 3: "palette", 4: "grayscale+alpha", 6: "rgba"}


def read_dds(header):
    if len(header) < 92 or header[:4] != b"DDS ":
        return None
    height, width = struct.unpack_from("<II", header, 12)
    mipmaps = struct.unpack_from("<I", header, 28)[0]
    pixel_flags = struct.unpack_from("<I", header, 80)[0]
    bit_count = struct.unpack_from("<I", header, 88)[0]
    if pixel_flags & DDPF_FOURCC:
        encoding = header[84:88].decode("ascii", "replace")
    else:
        encoding = f"uncompressed {bit_count}-bit"
    return {"width": width, "height": height, "detail": f"{encoding}, {max(mipmaps, 1)} mips"}


def read_png(header):
    if len(header) < 26 or header[:8] != bytes.fromhex("89504E470D0A1A0A"):
        return None
    width, height = struct.unpack_from(">II", header, 16)
    bit_depth, color_type = header[24], header[25]
    color_name = PNG_COLOR_TYPES.get(color_type, "unknown")
    return {"width": width, "height": height, "detail": f"{bit_depth}-bit {color_name}"}


def read_tga(header):
    if len(header) < 18:
        return None
    color_map_type, image_type = header[1], header[2]
    width, height = struct.unpack_from("<HH", header, 12)
    bits_per_pixel = header[16]
    if color_map_type not in (0, 1) or image_type not in (1, 2, 3, 9, 10, 11):
        return None
    if bits_per_pixel not in (8, 15, 16, 24, 32) or width == 0 or height == 0:
        return None
    compression = "RLE" if image_type >= 9 else "raw"
    return {"width": width, "height": height, "detail": f"{bits_per_pixel}-bit {compression}"}


def read_bmp(header):
    if len(header) < 30 or header[:2] != b"BM":
        return None
    dib_size = struct.unpack_from("<I", header, 14)[0]
    if dib_size < 40:
        return None
    width, height = struct.unpack_from("<ii", header, 18)
    bits_per_pixel = struct.unpack_from("<H", header, 28)[0]
    return {"width": abs(width), "height": abs(height), "detail": f"{bits_per_pixel}-bit"}


READERS = {".dds": read_dds, ".png": read_png, ".tga": read_tga, ".bmp": read_bmp}


def read_texture(path, extension):
    try:
        with open(path, "rb") as file:
            header = file.read(HEADER_SIZE)
    except OSError:
        return None
    return READERS[extension](header)


def summarize(files, root_folder, oversized_limit):
    results = []
    for file in files:
        extension = file["extension"]
        if extension not in READERS:
            continue
        info = read_texture(os.path.join(root_folder, file["path"]), extension)
        if info is None:
            continue
        results.append({
            "path": file["path"],
            "size": file["size"],
            "format": extension.lstrip("."),
            **info,
            "oversized": max(info["width"], info["height"]) > oversized_limit,
        })
    return results
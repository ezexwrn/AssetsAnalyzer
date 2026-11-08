import os
import struct

try:
    from tinytag import TinyTag
except ImportError:
    TinyTag = None

OGG_HEADER_SIZE = 96
OGG_EXTENSIONS = {".ogg", ".oga"}
TINYTAG_EXTENSIONS = {".mp3", ".flac", ".m4a", ".opus", ".wma", ".ogg", ".oga"}
WAV_FORMATS = {
    1: "pcm",
    2: "ms adpcm",
    3: "float",
    0x11: "ima adpcm",
    0x55: "mp3",
    0x160: "wma",
    0x161: "wma",
    0x162: "wma",
    0xFFFE: "extensible",
}
LOSSLESS_WAV_FORMATS = {"pcm", "float"}


def read_wav(path):
    fmt = None
    data_size = None
    try:
        with open(path, "rb") as file:
            header = file.read(12)
            if len(header) < 12 or header[:4] != b"RIFF" or header[8:12] != b"WAVE":
                return None
            while fmt is None or data_size is None:
                chunk_header = file.read(8)
                if len(chunk_header) < 8:
                    break
                chunk_id, chunk_size = struct.unpack("<4sI", chunk_header)
                skip = chunk_size + chunk_size % 2
                if chunk_id == b"fmt ":
                    if chunk_size < 16:
                        return None
                    fmt = file.read(16)
                    file.seek(skip - 16, os.SEEK_CUR)
                elif chunk_id == b"data":
                    data_size = chunk_size
                    file.seek(skip, os.SEEK_CUR)
                else:
                    file.seek(skip, os.SEEK_CUR)
    except OSError:
        return None

    if fmt is None or len(fmt) < 16:
        return None

    format_tag = struct.unpack_from("<H", fmt, 0)[0]
    channels = struct.unpack_from("<H", fmt, 2)[0]
    sample_rate = struct.unpack_from("<I", fmt, 4)[0]
    byte_rate = struct.unpack_from("<I", fmt, 8)[0]
    format_name = WAV_FORMATS.get(format_tag, f"tag 0x{format_tag:04x}")
    return {
        "format": format_name,
        "lossless": format_name in LOSSLESS_WAV_FORMATS,
        "channels": channels,
        "sample_rate": sample_rate,
        "bitrate_kbps": byte_rate * 8 / 1000 if byte_rate else None,
        "duration": data_size / byte_rate if data_size is not None and byte_rate else None,
    }


def read_ogg(path):
    try:
        with open(path, "rb") as file:
            header = file.read(OGG_HEADER_SIZE)
    except OSError:
        return None

    if header[:4] != b"OggS":
        return None
    marker = header.find(b"\x01vorbis")
    if marker == -1 or len(header) < marker + 24:
        return None

    channels = header[marker + 11]
    sample_rate = struct.unpack_from("<I", header, marker + 12)[0]
    nominal_bitrate = struct.unpack_from("<i", header, marker + 20)[0]
    return {
        "format": "ogg vorbis",
        "channels": channels,
        "sample_rate": sample_rate,
        "bitrate_kbps": nominal_bitrate / 1000 if nominal_bitrate > 0 else None,
        "duration": None,
        "lossless": False,
    }


def _format_label(extension, mime_type):
    if extension in OGG_EXTENSIONS:
        codec = mime_type.partition('codecs="')[2].rstrip('"')
        return f"ogg {codec}" if codec else "ogg"
    return extension.lstrip(".")


def read_tinytag(path, extension):
    try:
        tag = TinyTag.get(path, tags=False, image=False)
    except Exception:
        # A parser bug or a corrupt file must not stop the whole scan.
        return None

    if tag.samplerate is None:
        return None

    return {
        "format": _format_label(extension, tag.mime_type or ""),
        "lossless": bool(tag.is_lossless),
        "channels": tag.channels,
        "sample_rate": tag.samplerate,
        "bitrate_kbps": tag.bitrate or None,
        "duration": tag.duration,
    }


def supported_extensions():
    extensions = {".wav"} | OGG_EXTENSIONS
    if TinyTag is not None:
        extensions |= TINYTAG_EXTENSIONS
    return extensions


def read_audio(path, extension):
    if extension == ".wav":
        return read_wav(path)
    if TinyTag is not None and extension in TINYTAG_EXTENSIONS:
        info = read_tinytag(path, extension)
        if info is not None:
            return info
    if extension in OGG_EXTENSIONS:
        return read_ogg(path)
    return None


def summarize(files, root_folder, target_kbps):
    supported = supported_extensions()
    results = []
    for file in files:
        extension = file["extension"]
        if extension not in supported:
            continue
        info = read_audio(os.path.join(root_folder, file["path"]), extension)
        if info is None:
            continue
        convertible = info["lossless"] and info["duration"] is not None
        estimated = int(info["duration"] * target_kbps * 1000 / 8) if convertible else None
        results.append({
            "path": file["path"],
            "size": file["size"],
            **info,
            "convertible": convertible,
            "estimated_saving": max(file["size"] - estimated, 0) if convertible else 0,
        })
    return results
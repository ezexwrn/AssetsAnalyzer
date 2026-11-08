import os
import struct

EXECUTABLES_CATEGORY = "executables"
MACHINES = {
    0x014C: "x86 (32-bit)",
    0x8664: "x64 (64-bit)",
    0x01C0: "arm (32-bit)",
    0xAA64: "arm64 (64-bit)",
}
IMAGE_FILE_LARGE_ADDRESS_AWARE = 0x0020
IMAGE_FILE_DLL = 0x2000
NOT_PE = {"machine": "not a PE file", "is_dll": False, "large_address_aware": False}


def read_pe(path):
    try:
        with open(path, "rb") as file:
            dos_header = file.read(64)
            if len(dos_header) < 64 or dos_header[:2] != b"MZ":
                return None
            pe_offset = struct.unpack_from("<I", dos_header, 0x3C)[0]
            file.seek(pe_offset)
            header = file.read(24)
    except OSError:
        return None

    if len(header) < 24 or header[:4] != b"PE\x00\x00":
        return None

    machine = struct.unpack_from("<H", header, 4)[0]
    characteristics = struct.unpack_from("<H", header, 22)[0]
    return {
        "machine": MACHINES.get(machine, f"unknown (0x{machine:04x})"),
        "is_dll": bool(characteristics & IMAGE_FILE_DLL),
        "large_address_aware": bool(characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE),
    }


def summarize(files, root_folder):
    results = []
    for file in files:
        if file["category"] != EXECUTABLES_CATEGORY:
            continue
        info = read_pe(os.path.join(root_folder, file["path"])) or NOT_PE
        is_32_bit_exe = info["machine"].startswith("x86") and not info["is_dll"]
        results.append({
            "path": file["path"],
            "size": file["size"],
            **info,
            "laa_candidate": is_32_bit_exe and not info["large_address_aware"],
        })
    return results
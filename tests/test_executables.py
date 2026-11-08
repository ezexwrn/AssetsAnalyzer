import os
import struct
import tempfile
import unittest

from modules import executables, inventory
from tests.helpers import write_file

MACHINE_X86 = 0x014C
MACHINE_X64 = 0x8664
FLAG_EXECUTABLE = 0x0002
FLAG_LARGE_ADDRESS_AWARE = 0x0020
FLAG_DLL = 0x2000


def build_pe(machine, characteristics):
    dos_header = b"MZ" + bytes(58) + struct.pack("<I", 64)
    coff_header = struct.pack("<HHIIIHH", machine, 0, 0, 0, 0, 0, characteristics)
    return dos_header + b"PE\x00\x00" + coff_header


class ExecutablesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = temp.name

    def read(self, content):
        return executables.read_pe(write_file(self.root, "sample.exe", content))

    def test_32_bit_exe_without_large_address_aware(self):
        info = self.read(build_pe(MACHINE_X86, FLAG_EXECUTABLE))
        self.assertEqual(info, {"machine": "x86 (32-bit)", "is_dll": False, "large_address_aware": False})

    def test_large_address_aware_flag(self):
        info = self.read(build_pe(MACHINE_X86, FLAG_EXECUTABLE | FLAG_LARGE_ADDRESS_AWARE))
        self.assertTrue(info["large_address_aware"])

    def test_dll_flag(self):
        info = self.read(build_pe(MACHINE_X86, FLAG_EXECUTABLE | FLAG_DLL))
        self.assertTrue(info["is_dll"])

    def test_64_bit_machine(self):
        self.assertEqual(self.read(build_pe(MACHINE_X64, FLAG_EXECUTABLE))["machine"], "x64 (64-bit)")

    def test_unknown_machine_keeps_its_code(self):
        self.assertEqual(self.read(build_pe(0x1234, FLAG_EXECUTABLE))["machine"], "unknown (0x1234)")

    def test_files_that_are_not_pe_return_none(self):
        self.assertIsNone(self.read(b"hello"))
        self.assertIsNone(self.read(b"MZ" + bytes(100)))
        self.assertIsNone(executables.read_pe(os.path.join(self.root, "missing.exe")))

    def test_summarize_flags_32_bit_exe_candidates_only(self):
        write_file(self.root, "game.exe", build_pe(MACHINE_X86, FLAG_EXECUTABLE))
        write_file(self.root, "lib.dll", build_pe(MACHINE_X86, FLAG_EXECUTABLE | FLAG_DLL))
        write_file(self.root, "fake.exe", b"not a program")
        write_file(self.root, "notes.txt", b"hello")
        files = inventory.scan(self.root, {"executables": {".exe", ".dll"}})
        results = {item["path"]: item for item in executables.summarize(files, self.root)}
        self.assertEqual(len(results), 3)
        self.assertTrue(results["game.exe"]["laa_candidate"])
        self.assertFalse(results["lib.dll"]["laa_candidate"])
        self.assertFalse(results["fake.exe"]["laa_candidate"])
        self.assertEqual(results["fake.exe"]["machine"], "not a PE file")


if __name__ == "__main__":
    unittest.main()
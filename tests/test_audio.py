import os
import struct
import tempfile
import unittest

from modules import audio, inventory
from tests.helpers import write_file

DATA_SIZE = 16000


def wav_bytes(format_tag=1, extra_chunk=b""):
    fmt = struct.pack("<HHIIHH", format_tag, 1, 8000, 16000, 2, 16)
    data = bytes(DATA_SIZE)
    body = (
        b"WAVE"
        + b"fmt " + struct.pack("<I", 16) + fmt
        + extra_chunk
        + b"data" + struct.pack("<I", len(data)) + data
    )
    return b"RIFF" + struct.pack("<I", len(body)) + body


def ogg_bytes(channels=2, sample_rate=44100, nominal_bitrate=128000):
    page_header = b"OggS" + bytes(24)
    identification = (
        b"\x01vorbis"
        + struct.pack("<I", 0)
        + bytes([channels])
        + struct.pack("<I", sample_rate)
        + struct.pack("<iii", 0, nominal_bitrate, 0)
    )
    return page_header + identification


class AudioTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = temp.name

    def test_pcm_wav(self):
        info = audio.read_wav(write_file(self.root, "a.wav", wav_bytes()))
        self.assertEqual(info["format"], "pcm")
        self.assertEqual(info["channels"], 1)
        self.assertEqual(info["sample_rate"], 8000)
        self.assertEqual(info["bitrate_kbps"], 128.0)
        self.assertEqual(info["duration"], 1.0)

    def test_wav_with_odd_sized_chunk_before_data(self):
        extra = b"LIST" + struct.pack("<I", 3) + b"abc" + b"\x00"
        info = audio.read_wav(write_file(self.root, "a.wav", wav_bytes(extra_chunk=extra)))
        self.assertEqual(info["duration"], 1.0)

    def test_wav_with_other_format_tags(self):
        self.assertEqual(audio.read_wav(write_file(self.root, "a.wav", wav_bytes(2)))["format"], "ms adpcm")
        self.assertEqual(audio.read_wav(write_file(self.root, "b.wav", wav_bytes(0x1234)))["format"], "tag 0x1234")

    def test_invalid_wav(self):
        self.assertIsNone(audio.read_wav(write_file(self.root, "a.wav", b"not a wav file at all")))
        self.assertIsNone(audio.read_wav(os.path.join(self.root, "missing.wav")))

    def test_ogg_vorbis(self):
        info = audio.read_ogg(write_file(self.root, "a.ogg", ogg_bytes()))
        self.assertEqual(info["format"], "ogg vorbis")
        self.assertEqual(info["channels"], 2)
        self.assertEqual(info["sample_rate"], 44100)
        self.assertEqual(info["bitrate_kbps"], 128.0)
        self.assertIsNone(info["duration"])

    def test_invalid_ogg(self):
        self.assertIsNone(audio.read_ogg(write_file(self.root, "a.ogg", b"OggS but nothing else")))
        self.assertIsNone(audio.read_ogg(write_file(self.root, "b.ogg", b"hello")))

    def test_summarize_estimates_savings_only_for_uncompressed_audio(self):
        write_file(self.root, "pcm.wav", wav_bytes())
        write_file(self.root, "adpcm.wav", wav_bytes(2))
        write_file(self.root, "music.ogg", ogg_bytes())
        write_file(self.root, "broken.wav", b"garbage")
        files = inventory.scan(self.root, {})
        results = {item["path"]: item for item in audio.summarize(files, self.root, 32)}
        self.assertEqual(set(results), {"pcm.wav", "adpcm.wav", "music.ogg"})

        pcm_size = os.path.getsize(os.path.join(self.root, "pcm.wav"))
        self.assertTrue(results["pcm.wav"]["convertible"])
        self.assertEqual(results["pcm.wav"]["estimated_saving"], pcm_size - 4000)
        self.assertFalse(results["adpcm.wav"]["convertible"])
        self.assertEqual(results["adpcm.wav"]["estimated_saving"], 0)
        self.assertEqual(results["music.ogg"]["estimated_saving"], 0)


if __name__ == "__main__":
    unittest.main()
import os
import struct
import tempfile
import unittest
from unittest import mock

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


def mp3_bytes(frames=100):
    frame = bytes([0xFF, 0xFB, 0x90, 0x00]) + bytes(413)
    return frame * frames


def flac_bytes(sample_rate=44100, channels=2, bits_per_sample=16, total_samples=441000, audio_size=0):
    packed = (
        (sample_rate << 44)
        | ((channels - 1) << 41)
        | ((bits_per_sample - 1) << 36)
        | total_samples
    )
    streaminfo = struct.pack(">HH", 4096, 4096) + bytes(6) + struct.pack(">Q", packed) + bytes(16)
    return b"fLaC" + bytes([0x80]) + struct.pack(">I", len(streaminfo))[1:] + streaminfo + bytes(audio_size)


class AudioTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = temp.name

    def test_pcm_wav(self):
        info = audio.read_wav(write_file(self.root, "a.wav", wav_bytes()))
        self.assertEqual(info["format"], "pcm")
        self.assertTrue(info["lossless"])
        self.assertEqual(info["channels"], 1)
        self.assertEqual(info["sample_rate"], 8000)
        self.assertEqual(info["bitrate_kbps"], 128.0)
        self.assertEqual(info["duration"], 1.0)

    def test_wav_with_odd_sized_chunk_before_data(self):
        extra = b"LIST" + struct.pack("<I", 3) + b"abc" + b"\x00"
        info = audio.read_wav(write_file(self.root, "a.wav", wav_bytes(extra_chunk=extra)))
        self.assertEqual(info["duration"], 1.0)

    def test_wav_with_other_format_tags(self):
        adpcm = audio.read_wav(write_file(self.root, "a.wav", wav_bytes(2)))
        self.assertEqual(adpcm["format"], "ms adpcm")
        self.assertFalse(adpcm["lossless"])
        self.assertEqual(audio.read_wav(write_file(self.root, "b.wav", wav_bytes(0x1234)))["format"], "tag 0x1234")

    def test_invalid_wav(self):
        self.assertIsNone(audio.read_wav(write_file(self.root, "a.wav", b"not a wav file at all")))
        self.assertIsNone(audio.read_wav(os.path.join(self.root, "missing.wav")))

    def test_ogg_vorbis(self):
        info = audio.read_ogg(write_file(self.root, "a.ogg", ogg_bytes()))
        self.assertEqual(info["format"], "ogg vorbis")
        self.assertFalse(info["lossless"])
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


@unittest.skipIf(audio.TinyTag is None, "tinytag is not installed")
class TinyTagAudioTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = temp.name

    def test_mp3(self):
        info = audio.read_audio(write_file(self.root, "a.mp3", mp3_bytes()), ".mp3")
        self.assertEqual(info["format"], "mp3")
        self.assertFalse(info["lossless"])
        self.assertEqual(info["channels"], 2)
        self.assertEqual(info["sample_rate"], 44100)
        self.assertAlmostEqual(info["bitrate_kbps"], 128, delta=1)
        self.assertAlmostEqual(info["duration"], 2.6, delta=0.1)

    def test_flac(self):
        info = audio.read_audio(write_file(self.root, "a.flac", flac_bytes()), ".flac")
        self.assertEqual(info["format"], "flac")
        self.assertTrue(info["lossless"])
        self.assertEqual(info["channels"], 2)
        self.assertEqual(info["sample_rate"], 44100)
        self.assertEqual(info["duration"], 10.0)

    def test_corrupt_files_are_skipped(self):
        for name in ("a.mp3", "b.flac", "c.m4a", "d.wma", "e.opus"):
            path = write_file(self.root, name, b"this is not audio" * 10)
            self.assertIsNone(audio.read_audio(path, "." + name.split(".")[1]), name)

    def test_ogg_falls_back_to_the_own_reader_when_tinytag_cannot_parse_it(self):
        info = audio.read_audio(write_file(self.root, "a.ogg", ogg_bytes()), ".ogg")
        self.assertEqual(info["format"], "ogg vorbis")
        self.assertIsNone(info["duration"])

    def test_lossless_files_other_than_wav_are_conversion_candidates(self):
        write_file(self.root, "song.flac", flac_bytes(audio_size=500000))
        write_file(self.root, "song.mp3", mp3_bytes())
        files = inventory.scan(self.root, {})
        results = {item["path"]: item for item in audio.summarize(files, self.root, 32)}
        flac_size = os.path.getsize(os.path.join(self.root, "song.flac"))
        self.assertTrue(results["song.flac"]["convertible"])
        self.assertEqual(results["song.flac"]["estimated_saving"], flac_size - 40000)
        self.assertFalse(results["song.mp3"]["convertible"])


class WithoutTinyTagTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = temp.name

    def test_only_wav_and_ogg_are_supported(self):
        with mock.patch.object(audio, "TinyTag", None):
            self.assertEqual(audio.supported_extensions(), {".wav", ".ogg", ".oga"})

    def test_summarize_keeps_ogg_and_skips_the_formats_that_need_tinytag(self):
        write_file(self.root, "song.mp3", mp3_bytes())
        write_file(self.root, "music.ogg", ogg_bytes())
        files = inventory.scan(self.root, {})
        with mock.patch.object(audio, "TinyTag", None):
            results = audio.summarize(files, self.root, 96)
        self.assertEqual([item["path"] for item in results], ["music.ogg"])


if __name__ == "__main__":
    unittest.main()
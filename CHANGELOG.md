# Changelog

## 1.1.0
- Audio analysis for MP3, FLAC, M4A, Opus and WMA, and OGG durations, using the optional `tinytag` library.
- Lossless files (WAV, FLAC) are flagged as conversion candidates.
- Optional libraries are loaded from `libs/`.

## 1.0.0
- Unit tests with `unittest`.
- Complete README and this changelog.

## 0.8.0
- Portable launchers (`run.bat`, `run.sh`).
- Support for bundled embeddable Python in `runtime/`.
- Release packaging script.

## 0.7.0
- Audio analysis: WAV and OGG metadata and conversion estimate.

## 0.6.0
- Texture analysis: format, resolution and oversized detection.

## 0.5.0
- Executable analysis: architecture and Large Address Aware flag.

## 0.4.0
- File type detection by signature.

## 0.3.0
- Duplicate detection.

## 0.2.0
- Categories moved to `config.json`.
- JSON and HTML reports, and the `compare` command.

## 0.1.0
- Folder inventory by category, extension and top-level folder.
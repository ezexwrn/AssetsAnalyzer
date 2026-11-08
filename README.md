# AssetsAnalyzer

Portable tool that analyzes game/program folders to find where the weight is
(textures, audio, video, packed files) before optimizing them for low-end hardware.

## Usage

    run.bat <game_folder>            (Windows; you can drag a folder onto run.bat)
    sh run.sh <game_folder>          (Linux/macOS)
    run.bat compare <old_report.json> <new_report.json>

Reports are saved in `reports/` (JSON and HTML). Categories can be edited in `config.json`.

## Portable

Everything lives in one folder: copy it anywhere (a USB drive included).
Reports are saved next to the program in `reports/`.
If a `runtime/` folder with the embeddable Python is present, it is used;
otherwise the system Python (3.8+) is used.

## Tests

    python -m unittest discover -s tests -t .

## Status

Stage 1 done: folder inventory by category, extension and top-level folder.
Stage 2 done: reports (JSON/HTML) and report comparison.
Stage 3 done: duplicate detection.
Stage 4 done: file type detection by signature (magic bytes).
Stage 5 done: executable analysis (architecture, Large Address Aware).
Stage 6 done: texture analysis (format, resolution, oversized detection).
Stage 7 done: audio analysis (WAV and OGG metadata, conversion estimate).
Stage 8 done: portable launchers and release packaging.
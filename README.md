# AssetsAnalyzer

Portable tool that analyzes game/program folders to find where the weight is
(textures, audio, video, packed files) before optimizing them for low-end hardware.

## Usage

    python analyzer.py scan <game_folder>
    python analyzer.py compare <old_report.json> <new_report.json>

Reports are saved in `reports/` (JSON and HTML). Categories can be edited in `config.json`.

## Status

Stage 1 done: folder inventory by category, extension and top-level folder.
Stage 2 done: reports (JSON/HTML) and report comparison.

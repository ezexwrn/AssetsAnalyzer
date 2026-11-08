# Assets Analyzer

Portable tool that analyzes the folder of a game or program and shows where its
weight is, before you optimize it for low-end hardware.

It only **reads** files: it never modifies or deletes anything in the analyzed
folder. Reports are written next to the program, in `reports/`.

## What it reports

| Section | What it tells you |
|---|---|
| By category | Size and file count for textures, audio, video, executables, packed files, etc. |
| By top-level folder | Which folders hold the weight |
| Extensions in 'other' | What the uncategorized files are, by extension |
| Executables | Architecture (32/64-bit), EXE or DLL, *Large Address Aware* flag, and which 32-bit executables are candidates for it |
| Audio | Format, channels, sample rate and bitrate of loose WAV/OGG files, plus an estimated saving if uncompressed audio were converted |
| Textures | Format and resolution of loose DDS/PNG/TGA/BMP files, flagging oversized ones |
| Detected file types | The real type of each file read from its first bytes (signature), regardless of extension; unknown formats show their first bytes so you can look them up |
| Duplicates | Groups of identical files and the space they take |
| Heaviest files | The biggest files in the folder |

## Quick start

Windows:

    run.bat "C:\Games\MyGame"

You can also double-click `run.bat` and paste or drag a folder into the window,
or drag a folder onto `run.bat`.

Linux/macOS:

    sh run.sh /path/to/game

Options:

    run.bat "C:\Games\MyGame" --top 50     (list the 50 heaviest files)

Each analysis is saved in `reports/` as a JSON file (for comparing) and an HTML
file (for reading). To measure what an optimization saved, analyze the folder
before and after and compare the two JSON reports:

    run.bat compare reports\old.json reports\new.json

## Configuration

Everything adjustable lives in `config.json`:

| Key | Meaning |
|---|---|
| `categories` | Which extensions belong to each category (lowercase, with the dot) |
| `top_files` | How many heaviest files to list (`--top` overrides it) |
| `top_folders` | How many top-level folders to list |
| `duplicates_min_size` | Files smaller than this (in bytes) are ignored when looking for duplicates |
| `signature_categories` | Categories whose files get signature detection |
| `texture_oversized` | Textures with a side longer than this (in pixels) are flagged |
| `audio_target_kbps` | Bitrate used to estimate the saving of converting uncompressed audio |

## Portable use

The whole program lives in one folder: copy it anywhere, a USB drive included.
It needs Python 3.8 or newer (standard library only; developed and tested on
3.14). On a PC without Python, bundle the embeddable version:

1. Download the Windows embeddable package of Python from python.org and unzip
   it into `runtime/` so that `runtime\python.exe` exists.
2. Open `runtime\python3XX._pth` (XX is the version) and add a line with `..`
   at the end, so Python can find the `modules/` folder.

`run.bat` uses `runtime\python.exe` if it exists and the system Python otherwise.

To build a release `.zip` (it includes `runtime/` if present):

    python scripts/build_release.py <version>

## Limitations

- Container formats (`.img`, `.pak`, `.bin`, etc.) are not opened: the tool sees
  the container, not what is inside. Textures and audio inside them are not
  analyzed.
- Textures: only loose `.dds`, `.png`, `.tga` and `.bmp`. The DDS, TGA and BMP
  readers were tested with synthetic headers, not yet with real game files.
- Audio: WAV and OGG Vorbis only. MP3 is not analyzed and the duration of OGG
  files is not computed. The estimated saving is a rough approximation.
- Executables: only Windows (PE) files. "LAA candidate" marks every 32-bit `.exe`
  without the flag, installers and launchers included, so judge which one is the
  game.
- A duplicate is not necessarily removable: a game may reference every copy by
  its path. The tool reports, it does not decide.

## Tests

    python -m unittest discover -s tests -t .

## Project layout

    analyzer.py          entry point
    config.json          categories and thresholds
    run.bat, run.sh      launchers
    modules/             inventory, duplicates, signatures, executables,
                         textures, audio, report
    scripts/             release packaging
    tests/               unit tests
    reports/             generated reports (not in the repository)
    runtime/             optional embeddable Python (not in the repository)

## License

See `LICENSE`.
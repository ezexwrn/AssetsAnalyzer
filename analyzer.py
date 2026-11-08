import argparse
import json
import os
import sys

sys.dont_write_bytecode = True

from modules import inventory, report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
REPORTS_FOLDER = os.path.join(BASE_DIR, "reports")


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as config_file:
        return json.load(config_file)


def run_scan(args, config):
    if not os.path.isdir(args.folder):
        print(f"Folder not found: {args.folder}")
        return

    categories = {name: set(extensions) for name, extensions in config["categories"].items()}
    print("Scanning (hashing duplicate candidates can take a while on slow disks)...")
    files = inventory.scan(args.folder, categories)
    data = report.build(args.folder, files, args.top, config)
    report.print_console(data, config["top_folders"])

    json_path, html_path = report.save(data, REPORTS_FOLDER, config["top_folders"])
    print(f"\nReports saved:\n  {json_path}\n  {html_path}")


def run_compare(args):
    for path in (args.old, args.new):
        if not os.path.isfile(path):
            print(f"Report not found: {path}")
            return

    report.print_comparison(report.load_json(args.old), report.load_json(args.new))


def main():
    config = load_config()

    parser = argparse.ArgumentParser(description="Assets Analyzer: find where the weight is in a game folder.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="analyze a game folder")
    scan_parser.add_argument("folder")
    scan_parser.add_argument("--top", type=int, default=config["top_files"], help="how many heaviest files to list")

    compare_parser = subparsers.add_parser("compare", help="compare two JSON reports")
    compare_parser.add_argument("old")
    compare_parser.add_argument("new")

    argv = sys.argv[1:]
    if not argv:
        parser.print_help()
        return
    if argv[0] not in ("scan", "compare", "-h", "--help"):
        argv.insert(0, "scan")
    args = parser.parse_args(argv)
    if args.command == "scan":
        run_scan(args, config)
    else:
        run_compare(args)


if __name__ == "__main__":
    main()
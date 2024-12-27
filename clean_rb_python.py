import argparse
import xml.etree.ElementTree as ET
import os
from pathlib import Path
from datetime import datetime
from typing import List

parser = argparse.ArgumentParser(
    prog="clean_rb_python",
    description="Deletes files from your Rekordbox folder which are not in the library based on an exported Rekordbox XML",
    add_help=True,
)
parser.add_argument(
    "rekordbox_xml",
    help="The file name of the XML file from Rekordbox",
)
parser.add_argument(
    "-c", "--clean", action="store_true", help="do the cleaning", default=False
)
parser.add_argument(
    "-s",
    "--simulate",
    action="store_true",
    help="simulate the cleaning to see what would be deleted (default behaviour)",
    default=True,
)
parser.add_argument(
    "--skip",
    type=str,
    action="store",
    default=None,
    help="skip the cleaning for these strings in the paths, divided by ',' (applies to both the local files and the paths in the XML file)",
)
parser.add_argument(
    "--include-streaming",
    action="store_true",
    help="include stored streaming service file urls (they are skipped by adding 'tidal', 'soundcloud', 'beatport', 'itunes' to the skip list by default)",
    default=False,
)
parser.add_argument(
    "--details",
    action="store_true",
    help="show the detailed results (per file) on console instead of a summary",
    default=False,
)
parser.add_argument(
    "--results-file",
    action="store_true",
    help="write the deatiled results to a text file: either clean_results_<datetime>.txt or simulate_results_<datetime>.txt",
    default=False,
)
parser.add_argument("--version", action="version", version="%(prog)s 0.9")
args = parser.parse_args()


def should_skip_path(path: str):
    skips: List[str] = []
    if not args.include_streaming:
        skips.append("tidal")
        skips.append("soundcloud")
        skips.append("beatport")
        skips.append("itunes")
    if args.skip:
        for s in args.skip.split(","):
            skips.append(s)
    if skips:
        for s in skips:
            if s in path:
                return True
    return False


def get_path_list_from_rekordbox_xml():
    try:
        with open(args.rekordbox_xml, "r", encoding="utf-8") as rxml:
            xml_tree = ET.parse(rxml)
    except FileNotFoundError:
        print("File not found")
        exit(1)
    except ET.ParseError:
        print("Invalid XML file")
        exit(1)
    xml_tracks = list(xml_tree.iter("TRACK"))
    if not xml_tracks:
        print("No xml_tracks found in the XML file")
        exit(1)

    xml_paths: List[str] = []
    for track in xml_tracks:
        location = track.get("Location")
        if location and not should_skip_path(location):
            xml_paths.append(
                location.replace("file://localhost/", "").replace("/", os.sep)
            )

    return xml_paths


def determine_common_path(paths: List[str]):
    common_path: str = ""
    for path in paths:
        if common_path == "":
            common_path = path
        else:
            for i in range(len(common_path)):
                if common_path[i] != path[i]:
                    common_path = common_path[:i]
                    break
    return common_path


def should_delete_file(file_path: Path, xml_paths: List[str]):
    return str(file_path.resolve()) not in xml_paths


# The main code starts here
# -------------------------


xml_paths = get_path_list_from_rekordbox_xml()

common_path = determine_common_path(xml_paths)
print(
    f"\nThe common path in the XML file is:\n{common_path}\nDo you want to {"clean" if args.clean else "simulate cleaning"} this folder?\n\n(Y)es / (N)o"
)
inp: str = ""
while True:
    inp = input().lower()
    if inp not in ("y", "n"):
        print("Please enter 'Y' or 'N' to answer the question")
    else:
        break
if inp == "n":
    print("\nPlease enter the path you want to clean:")
    while True:
        input_path = input().strip().replace('"', "")
        if not os.path.exists(input_path):
            print("The path does not exist. Please enter a valid path.")
        elif common_path not in input_path:
            print(
                "The path does not contain the common path of the XML file. Please enter a valid path."
            )
        else:
            break
    common_path = input_path
inp = ""


print(
    f"\nStarting to {"clean" if args.clean else "simulate cleaning"} from folder {common_path}"
)
file_postfix = ""
if args.results_file:
    file_postfix = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(
        f"\nThe results will be written to the following file: {'clean' if args.clean else 'simulate'}_results_{file_postfix}.txt"
    )

if args.clean:
    print(
        "\nWE ARE ABOUT TO DELETE FILES FROM YOUR REKORDBOX LIBRARY! MAKE SURE YOUR LIBRARY IS BACKED UP\nDo you want to proceed?\n\n(Y)es / (N)o"
    )
    inp: str = ""
    while True:
        inp = input().lower()
        if inp not in ("y", "n"):
            print("Please enter 'Y' or 'N' to answer the question")
        else:
            break
    if inp == "n":
        print("\nOk, bye!")
        exit(0)

details = ""
details += (
    "\nDeleted files:\n--------------\n"
    if args.clean
    else "\nFiles to be deleted:\n--------------------\n"
)

deleted_files = 0
skipped_files = 0
for path in Path(common_path).rglob("*"):
    if path.is_file():
        if should_delete_file(path, xml_paths):
            details += f"\n{path.resolve()}"
            if args.clean:
                try:
                    path.unlink()
                    deleted_files += 1
                except FileNotFoundError:
                    skipped_files += 1
                    details += " (skipped)"
        else:
            skipped_files += 1
            details += f"\n{path.resolve()} (skipped)"

results = f"\nSUMMARY:\n========\nDeleted files: {deleted_files}\nSkipped files: {skipped_files}\n"

xml_paths_not_found: List[str] = []
for xml_path in xml_paths:
    if not os.path.exists(xml_path):
        xml_paths_not_found.append(xml_path)
if len(xml_paths_not_found) > 0:
    details += (
        "\n\nPaths in the XML file not found:\n--------------------------------\n"
    )
    for notfound in xml_paths_not_found:
        details += f"\n{notfound}"
results += f"Paths in the XML file not found: {len(xml_paths_not_found)}\n"

print(results)

if args.details or args.results_file:
    if args.details:
        print(details)
    if args.results_file:
        results += details
        with open(
            f"{'clean' if args.clean else 'simulate'}_results_{file_postfix}.txt",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(results)

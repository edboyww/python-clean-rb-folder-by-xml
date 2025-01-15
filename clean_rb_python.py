__version__ = "1.0.0"

import argparse
import xml.etree.ElementTree as ET
import os
from pathlib import Path
from datetime import datetime
from typing import List
from urllib.parse import unquote
from prompt_toolkit import prompt
from prompt_toolkit.completion import NestedCompleter

# Parse the command line arguments
#
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
    "--skip-folder",
    type=str,
    action="store",
    default=None,
    help="skip the cleaning for these strings in the folder paths, divided by ',' (applies to both the local files and the paths in the XML file)",
)
parser.add_argument(
    "--details",
    action="store_true",
    help="show the detailed results (per file) on console instead of a summary",
    default=False,
)
parser.add_argument(
    "--details-file",
    action="store_true",
    help="write the deatiled results to a text file: either clean_results_<datetime>.txt or simulate_results_<datetime>.txt",
    default=False,
)
parser.add_argument(
    "--check-xml",
    action="store_true",
    help="check if the XML has any URLs which does not exist in the filesystem",
    default=False,
)
parser.add_argument("--version", action="version", version="%(prog)s 1.1")
args = parser.parse_args()

SEP = os.path.sep


# Function to determine if a path should be skipped based on the skip list and the include_streaming flag
def should_skip_path(input_arg: Path | str):
    parent_str = ""
    input_path = None
    if type(input_arg) is str:
        input_path = Path(input_arg)
    elif type(input_arg) is Path:
        input_path = input_arg
    else:
        return True
    if input_path:
        parent_str = f"{input_path.parent}"
    else:
        return True

    # Check folder
    if args.skip_folder:
        skip_folders: List[str] = []
        for s in args.skip_folder.split(","):
            skip_folders.append(s.lower())
        for skip in skip_folders:
            if skip in parent_str.lower():
                return True

    return False


# Function to get the list of paths from the Rekordbox XML file
#
def get_path_list_from_rekordbox_xml():
    try:
        with open(args.rekordbox_xml, "r", encoding="utf-8") as rxml:
            xml_tree = ET.parse(rxml)
    except FileNotFoundError:
        print("XML file not found")
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
        if location:
            raw_path = unquote(location.replace("file://localhost/", ""))
            # skip streaming urls
            if (
                raw_path.startswith("tidal:")
                or raw_path.startswith("soundcloud:")
                or raw_path.startswith("itunes:")
                or raw_path.startswith("beatsource:")
                or raw_path.startswith("beatport:")
            ):
                continue
            xml_paths.append(raw_path.replace("/", SEP))

    return xml_paths


# Function to determine the common path in a list of paths
#
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


# Build a dict of the folder structure for the autocomplete function
#
type AutocompleteDict = dict[str, AutocompleteDict | None]


# The function
def autocomplete_dict(path: Path) -> None | AutocompleteDict:
    iter_dir = [item for item in path.iterdir() if item.is_dir()]
    if len(iter_dir) == 0:
        return None
    else:
        folder_dict: AutocompleteDict = {}
        for item in iter_dir:
            try:
                folder_dict[item.name + SEP] = autocomplete_dict(item)
            except PermissionError:
                folder_dict[item.name + SEP] = None
        return folder_dict


# The main code starts here
# -------------------------

# Get the paths from the XML file and determine the root path for the cleaning process
xml_paths = get_path_list_from_rekordbox_xml()
initial_common_path = determine_common_path(xml_paths)
try:
    autocomplete_data = autocomplete_dict(Path(initial_common_path))
except PermissionError:
    print("ERROR: No permission to process common path in XML")
    exit(1)
common_path = initial_common_path
if autocomplete_data is not None:
    print(
        "\nSet the folder you want to clean starting with the common folder for all the files in the XML file. Press TAB to see the folders on a current level and SPACE to get to the next level. You can set the path by pressing ENTER.\n"
    )
    completer = NestedCompleter.from_nested_dict((autocomplete_data))

    while True:
        print("SELECT THE PATH:")
        input_raw = prompt(initial_common_path, completer=completer)
        input_path = input_raw.strip().replace(" ", "")
        common_path = initial_common_path + input_path
        if not os.path.exists(common_path):
            print("The path does not exist. Please enter a valid path.\n")
            continue
        print(
            f"\nThe selected path is\n{common_path}\nIS THE PATH OKAY? (Y)es / (N)o:",
            end=" ",
        )
        inp = input().lower()
        if inp not in ("y", "n"):
            print("Please enter 'Y' or 'N' to answer the question:", end=" ")
        elif inp == "y":
            break

# Message before starting the cleaning process, and determine the file postfix for the details file
print(
    f"\nStarting to {'clean' if args.clean else 'simulate cleaning'} from folder {common_path}"
)
file_postfix = ""
if args.details_file:
    file_postfix = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(
        f"The details will be written to the following file: {'clean' if args.clean else 'simulate'}_details_{file_postfix}.txt"
    )

# Ask for confirmation before actually deleting files

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


# Start the cleaning process

deleted_files = 0
deleted_details = (
    "\n\nDeleted files:\n--------------\n"
    if args.clean
    else "\n\nFiles to be deleted:\n--------------------\n"
)
skipped_files = 0
skipped_details = "\n\n\nSkipped files:\n--------------\n"
for path in Path(common_path).rglob("*"):
    if path.is_file():
        resolved_entry = f"{path}"
        if should_skip_path(resolved_entry):
            skipped_files += 1
            skipped_details += f"\nS: {resolved_entry.replace(common_path, '')}"
        elif resolved_entry not in xml_paths:
            deleted_files += 1
            deleted_details += f"\nD: {resolved_entry.replace(common_path, '')}"
            if args.clean:
                path.unlink()  # THIS LINE DELETES THE FILE!

results = f"\nSUMMARY:\n========\n{'Deleted files' if args.clean else 'Files to be deleted'}: {deleted_files}\nSkipped files: {skipped_files}\n"

# Check if there are paths in the XML file that are not found (given the argument)
xml_paths_not_found: List[str] = []
xml_paths_not_found_details = ""
if args.check_xml:
    for xml_path in xml_paths:
        if not os.path.exists(xml_path):
            xml_paths_not_found.append(xml_path)
    if len(xml_paths_not_found) > 0:
        results += f"Paths in XML not found: {len(xml_paths_not_found)}"
        if args.details or args.details_file:
            xml_paths_not_found_details += "\n\n\nPaths in the XML file not found:\n---------------------------------\n"
            for notfound in xml_paths_not_found:
                xml_paths_not_found_details += f"\nX: {notfound}"

# Show the summary

print(results)

# Print the details if requested

if args.details or args.details_file:
    details = ""
    if deleted_files:
        details += deleted_details
    if skipped_files:
        details += skipped_details
    if args.check_xml and xml_paths_not_found:
        details += xml_paths_not_found_details
    if args.details:
        print(details)
    if args.details_file:
        results += details
        with open(
            f"{'clean' if args.clean else 'simulate'}_details_{file_postfix}.txt",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(results)

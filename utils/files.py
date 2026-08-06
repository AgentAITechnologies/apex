import os
import re
from datetime import datetime
import xml.etree.ElementTree as ET

from rich import print as rprint
from utils.console_io import debug_print as dprint

PRINT_PREFIX = "[bold][Files][/bold]"

def create_incrementing_directory(output_dir, prefix: str) -> str:
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Escape special regex characters in the prefix
    escaped_prefix = re.escape(prefix)
    
    # Get a list of existing directories matching the prefix
    existing_runs = [
        d for d in os.listdir(output_dir) 
        if os.path.isdir(os.path.join(output_dir, d)) and 
        re.match(rf"^{escaped_prefix}\d+$", d)
    ]
    
    # Find the next run number
    if existing_runs:
        run_numbers = [int(d[len(prefix):]) for d in existing_runs]
        next_run = max(run_numbers) + 1
    else:
        next_run = 1
    
    # Create the new run directory
    new_run_dir = os.path.join(output_dir, f"{prefix}{next_run}")
    os.makedirs(new_run_dir)
    
    return new_run_dir

def create_directory(directory: str) -> None:
    if not os.path.exists(directory):
        os.makedirs(directory)

def sort_filenames_ny_num(filenames: list[str], pattern: str) -> list[str]:
    def extract_num(filename):
        match = re.search(pattern, filename)
        return int(match.group(1)) if match else float('inf')

    sorted_filenames = sorted(filenames, key=extract_num)
    return sorted_filenames

def get_persistent_notes_file_path():
    OUTPUT_DIR = os.environ.get("OUTPUT_DIR")
    if not OUTPUT_DIR:
        error_message = f"{PRINT_PREFIX} OUTPUT_DIR not set"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise KeyError(error_message)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    PERSISTENT_NOTES_FILE_PATH = os.path.join(OUTPUT_DIR, "persistent_notes.xml")
    
    if not os.path.exists(PERSISTENT_NOTES_FILE_PATH):
        with open(PERSISTENT_NOTES_FILE_PATH, 'w') as file:
            file.write("")
    
    return PERSISTENT_NOTES_FILE_PATH

def read_persistent_notes() -> str:
    PERSISTENT_NOTES_FILE_PATH = get_persistent_notes_file_path()

    try:
        with open(PERSISTENT_NOTES_FILE_PATH, 'r') as file:
            persistent_notes = file.read()
        dprint(f"{PRINT_PREFIX} loaded persistent_notes:\n{persistent_notes}\n")

    except FileNotFoundError:
        error_message = f"{PRINT_PREFIX} persistent_notes.xml not found at {PERSISTENT_NOTES_FILE_PATH}"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise

    return persistent_notes

def write_persistent_note(persistent_note: str) -> None:
    PERSISTENT_NOTES_FILE_PATH = get_persistent_notes_file_path()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_note = persistent_note.strip()

    if formatted_note:
        try:
            elem = ET.fromstring(formatted_note)
            if "timestamp" not in elem.attrib:
                elem.attrib["timestamp"] = now_str
            formatted_note = ET.tostring(elem, encoding="unicode")
        except ET.ParseError:
            if "<timestamp>" not in formatted_note and 'timestamp="' not in formatted_note:
                formatted_note = f'<note timestamp="{now_str}">\n{formatted_note}\n</note>'

    try:
        with open(PERSISTENT_NOTES_FILE_PATH, 'a', encoding="utf-8") as file:
            file.write(f"\n{formatted_note}\n")
        dprint(f"{PRINT_PREFIX} wrote persistent_note: {formatted_note}")

    except FileNotFoundError:
        error_message = f"{PRINT_PREFIX} persistent_notes.xml not found at {PERSISTENT_NOTES_FILE_PATH}"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise

def clear_persistent_notes() -> None:
    PERSISTENT_NOTES_FILE_PATH = get_persistent_notes_file_path()

    try:
        with open(PERSISTENT_NOTES_FILE_PATH, 'w') as file:
            file.write("")
        dprint(f"{PRINT_PREFIX} cleared persistent_notes")

    except FileNotFoundError:
        error_message = f"{PRINT_PREFIX} persistent_notes.xml not found at {PERSISTENT_NOTES_FILE_PATH}"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise

def overwrite_persistent_notes(content: str) -> None:
    PERSISTENT_NOTES_FILE_PATH = get_persistent_notes_file_path()

    try:
        with open(PERSISTENT_NOTES_FILE_PATH, 'w') as file:
            file.write(content)
        dprint(f"{PRINT_PREFIX} overwrote persistent_notes")

    except FileNotFoundError:
        error_message = f"{PRINT_PREFIX} persistent_notes.xml not found at {PERSISTENT_NOTES_FILE_PATH}"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise
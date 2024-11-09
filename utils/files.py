import os
import re

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
        re.match(f"^{escaped_prefix}\d+$", d)
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

    try:
        with open(PERSISTENT_NOTES_FILE_PATH, 'a') as file:
            file.write(f"\n{persistent_note}\n")
        dprint(f"{PRINT_PREFIX} wrote persistent_note: {persistent_note}")

    except FileNotFoundError:
        error_message = f"{PRINT_PREFIX} persistent_notes.xml not found at {PERSISTENT_NOTES_FILE_PATH}"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise
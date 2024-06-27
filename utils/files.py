import os
import re

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
import os
import re

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def sort_filenames_ny_num(filenames, pattern):
    # Extract the number from the filename using a regular expression
    def extract_num(filename):
        match = re.search(pattern, filename)
        return int(match.group(1)) if match else float('inf')

    sorted_filenames = sorted(filenames, key=extract_num)
    return sorted_filenames
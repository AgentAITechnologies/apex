import re
import subprocess


def extract_python(markdown_string):
    pattern = re.compile(r"```python\n(.*?)```", re.DOTALL)
    match = pattern.search(markdown_string)
    if match:
        return match.group(1)
    else:
        return None

def exec_python(code):
    # Open a subprocess that runs Python, and send the code to its stdin
    process = subprocess.Popen(['python', '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    stdout, stderr = process.communicate()

    return stdout, stderr
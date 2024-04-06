import re
import subprocess



def exec_python(code):
    # Open a subprocess that runs Python, and send the code to its stdin
    process = subprocess.Popen(['python', '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    stdout, stderr = process.communicate()

    return stdout, stderr
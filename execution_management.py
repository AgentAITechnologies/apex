import re
import subprocess
import traceback


def exec_python(code):
    # Open a subprocess that runs Python, and send the code to its stdin
    process = subprocess.Popen(['python', '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    stdout, stderr = process.communicate()

    return stdout, stderr


def capture_python_output(csm, locals):
    parsed_response = locals.get("parsed_response")
    
    language_name = parsed_response["code_block"]["language_name"]
    code = parsed_response["code_block"]["code"]

    stdout, stderr = None, None

    if language_name == "python":
        try:
            stdout, stderr = exec_python(code)
        except Exception as e:
            error_message = traceback.format_exc()
            print(f"[main] Python script execution error for task \"{locals.get('task')}\":\n{error_message}")
            stderr = error_message

        print(f"[main] Python script execution results for task \"{locals.get('task')}\":\nstdout:\n{stdout}\nstderr:\n{stderr}")

    result = {
        "result": {
            "action": "execute python",
            "code": code,
            "output": {"stdout": stdout, "stderr": stderr}
        }
    }

    locals.get("memory").add_result(result)
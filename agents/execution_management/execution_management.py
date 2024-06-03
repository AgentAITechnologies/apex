import os
import io
import sys
from typing import Optional, Any
import dotenv
import shutil

from contextlib import redirect_stdout, redirect_stderr

from rich import print

from utils.files import create_directory, sort_filenames_ny_num

class CodeExecutor:
    PRINT_PREFIX: str = "[bold][CodeExecutor][/bold]"
    PRIOR_CODE_FILENAME: str = "prior_code.py"

    def __init__(self, prefix: Optional[str] = None, owner_name: Optional[str] = None) -> None:
        dotenv.load_dotenv()

        if prefix:
            self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"
        
        if owner_name:
            self.owner_name = owner_name

        self.SESSION_DIR = os.path.join(os.environ.get("SESSIONS_DIR"), self.owner_name)
        self.CODE_DIR = os.path.join(self.SESSION_DIR, os.environ.get("OUTPUT_DIR"))

        create_directory(self.CODE_DIR)

        self.execution_context: dict[str, Any] = {}

    def __del__(self):
        shutil.rmtree(self.SESSION_DIR)

    def write_code_step_file(self, code, step_num):
        file_path = os.path.join(self.CODE_DIR, f"step_{step_num}.py")

        with open(file_path, "w") as file:
            file.write(code)

    def execute_code_step(self, step_num) -> tuple[str, str]:
        file_path = os.path.join(self.CODE_DIR, f"step_{step_num}.py")

        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                code = file.read()

            stdout_capture, stderr_capture = io.StringIO(), io.StringIO()

            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    exec(code, {}, self.execution_context)
                except Exception as e:
                    stderr_capture.write(str(e))

            return stdout_capture.getvalue(), stderr_capture.getvalue()

        else:
            print(f"[red][bold]{self.PRINT_PREFIX} File {file_path} for step {step_num} execution not found.[/bold][/red]")
            exit(1)

    def execute_code_steps(self):
        step_num = 1

        while os.path.exists(os.path.join(self.CODE_DIR, f"step_{step_num}.py")):
            try:
                yield self.execute_code_step(step_num)
                step_num += 1
            except FileNotFoundError:
                print(f"[red][bold]{self.PRINT_PREFIX} Code for step {step_num} unable to be written to disk[/bold][/red]")
                break

    def finalize_task(self, task):
        with open(os.path.join(self.CODE_DIR, self.PRIOR_CODE_FILENAME), "a") as prior_code_file:
            prior_code_file.write(f"'''\n{task}\n'''\n")

            for dir, dirnames, filenames in os.walk(self.CODE_DIR):
                sorted_filenames = sort_filenames_ny_num(filenames, r'step_(\d+)\.py')

                for filename in sorted_filenames:
                    if filename == self.PRIOR_CODE_FILENAME:
                        continue

                    with open(os.path.join(self.CODE_DIR, filename), "r") as code_file:
                        prior_code_file.write(f"# <{filename.split('.')[0]}>\n")
                        prior_code_file.write(code_file.read().strip()+"\n")
                        prior_code_file.write(f"# </{filename.split('.')[0]}>\n\n")

                    os.remove(os.path.join(self.CODE_DIR, filename))

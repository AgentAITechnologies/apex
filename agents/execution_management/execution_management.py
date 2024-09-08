import os
import io
import sys
from typing import Any, TextIO
import dotenv
import shutil

from contextlib import redirect_stdout, redirect_stderr

from rich import print

from utils.files import create_directory, sort_filenames_ny_num


class TeeIO(io.StringIO):
    def __init__(self, console_output: TextIO) -> None:
        super().__init__()
        self.console_output = console_output

    def write(self, s: str) -> None:
        super().write(s)
        self.console_output.write(s)
        self.console_output.flush()


class CodeExecutor:
    PRINT_PREFIX: str = "[bold][CodeExecutor][/bold]"
    PRIOR_CODE_FILENAME: str = "prior_code.py"

    def __init__(self, prefix: str, owner_name: str) -> None:
        dotenv.load_dotenv()

        if prefix:
            self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"
        
        if not owner_name:
            error_message = f"{self.PRINT_PREFIX} owner_name not provided"
            print(f"[red][bold]{error_message}[/bold][/red]")
            raise ValueError(error_message)
        else:
            self.owner_name = owner_name

        SESSIONS_DIR = os.environ.get("SESSIONS_DIR")
        if not SESSIONS_DIR:
            error_message = f"{self.PRINT_PREFIX} SESSIONS_DIR not set in environment"
            print(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)
        
        self.SESSION_DIR: str = os.path.join(SESSIONS_DIR, self.owner_name)

        OUTPUT_DIR = os.environ.get("OUTPUT_DIR")
        if not OUTPUT_DIR:
            error_message = f"{self.PRINT_PREFIX} OUTPUT_DIR not set in environment"
            print(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)

        self.CODE_DIR = os.path.join(self.SESSION_DIR, OUTPUT_DIR)

        create_directory(self.CODE_DIR)

        self.execution_context: dict[str, Any] = {}

    def __del__(self):
        shutil.rmtree(self.SESSION_DIR)

    def write_code_step_file(self, code: str, step_num: int) -> None:
        file_path = os.path.join(self.CODE_DIR, f"step_{step_num}.py")

        with open(file_path, "w", errors="replace") as file:
            file.write(code)

    def execute_code_step(self, step_num: int) -> tuple[str, str]:
        file_path = os.path.join(self.CODE_DIR, f"step_{step_num}.py")

        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                code = file.read()

            stdout_capture, stderr_capture = TeeIO(sys.stdout), io.StringIO()

            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    exec(code, self.execution_context)
                except Exception as e:
                    stderr_capture.write(str(e))

            return stdout_capture.getvalue(), stderr_capture.getvalue()

        else:
            error_message = f"{self.PRINT_PREFIX} File {file_path} for step {step_num} execution not found."
            print(f"[red][bold]{error_message}[/bold][/red]")
            raise FileNotFoundError(error_message)

    def execute_code_steps(self):
        step_num = 1

        while os.path.exists(os.path.join(self.CODE_DIR, f"step_{step_num}.py")):
            try:
                yield self.execute_code_step(step_num)
                step_num += 1
            except FileNotFoundError as e:
                error_message = f"{self.PRINT_PREFIX} Code for step {step_num} unable to be written to disk"
                print(f"[red][bold]{error_message}[/bold][/red]")
                raise FileNotFoundError(error_message)
      
    def condense_code_files(self, task: str) -> None:
        with open(os.path.join(self.CODE_DIR, self.PRIOR_CODE_FILENAME), "a") as exec_result_file:
            exec_result_file.write(f"'''\n{task}\n'''\n")

            for dir, dirnames, filenames in os.walk(self.CODE_DIR):
                sorted_filenames = sort_filenames_ny_num(filenames, r'step_(\d+)\.py')

                for filename in sorted_filenames:
                    if filename == self.PRIOR_CODE_FILENAME:
                        continue

                    with open(os.path.join(self.CODE_DIR, filename), "r") as code_file:
                        exec_result_file.write(f"# <{filename.split('.')[0]}>\n")
                        exec_result_file.write(code_file.read().strip()+"\n")
                        exec_result_file.write(f"# </{filename.split('.')[0]}>\n\n")

                    os.remove(os.path.join(self.CODE_DIR, filename))
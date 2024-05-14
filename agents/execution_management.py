import multiprocessing
import multiprocessing.connection
import sys
import io

from rich import print

class CodeExecutor:
    PRINT_PREFIX: str = "[CodeExecutor]"

    def __init__(self, prefix: str):
        self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"
        
        self.parent_conn, self.child_conn = multiprocessing.Pipe()
        self.child = multiprocessing.Process(target=self.child_process, args=(self.child_conn,))
        self.child.start()

    def child_process(self, pipe: multiprocessing.connection.PipeConnection) -> None:
        while True:
            code: str = pipe.recv()
            if code == "STOP":
                pipe.send("DONE")  # Signal the parent that the child is done
                break
            try:
                # Capture stdout to a StringIO object
                stdout_buffer = io.StringIO()
                sys.stdout = stdout_buffer
                exec(code)
                sys.stdout = sys.__stdout__  # Restore stdout
                # Send the captured output back to the parent process
                pipe.send(stdout_buffer.getvalue())
            except Exception as e:
                pipe.send(f"Error executing code: {e}")

    def execute_code(self, code: str) -> str:
        self.parent_conn.send(code)
        output: str | Exception = self.parent_conn.recv()
        return output

    def stop(self) -> None:
        self.parent_conn.send("STOP")
        self.child.join()
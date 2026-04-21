import tempfile
import os
import subprocess
import sys
from typing import Tuple

class ExecutionService:
    def run_code(self, code: str, language: str = "python") -> Tuple[str, str, int]:
        """
        Runs code with a timeout and returns (stdout, stderr, exit_code).

        Note: For this demo we execute inside the backend container process
        to avoid Docker-in-Docker path mapping issues on Windows hosts.
        """
        # Create a temporary file for the code
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                if language == "python":
                    file_path = os.path.join(temp_dir, "main.py")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(code)

                    result = subprocess.run(
                        [sys.executable, file_path],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    return result.stdout, result.stderr, result.returncode

                if language == "cpp":
                    cpp_path = os.path.join(temp_dir, "main.cpp")
                    bin_path = os.path.join(temp_dir, "main")
                    with open(cpp_path, "w", encoding="utf-8") as f:
                        f.write(code)

                    compile_result = subprocess.run(
                        ["g++", "-std=c++17", cpp_path, "-O2", "-o", bin_path],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                    if compile_result.returncode != 0:
                        return "", compile_result.stderr, compile_result.returncode

                    run_result = subprocess.run(
                        [bin_path],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    return run_result.stdout, run_result.stderr, run_result.returncode

                return "", f"Language '{language}' is not supported.", 2

            except subprocess.TimeoutExpired:
                return "", "Execution timed out after 10 seconds.", 124

            except Exception as e:
                return "", str(e), -1

execution_service = ExecutionService()

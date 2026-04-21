import tempfile
import os
import json
from typing import Dict, Any, List
import subprocess
import sys

class StaticAnalyzer:
    def analyze(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Runs static analysis on code and returns structured results.
        """
        suffix = '.cpp' if language == 'cpp' else '.py'
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            issues: List[Dict[str, Any]] = []

            try:
                if language == "cpp":
                    proc = subprocess.run(
                        [
                            "g++",
                            "-std=c++17",
                            "-Wall",
                            "-Wextra",
                            "-fsyntax-only",
                            tmp_path,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    stderr = (proc.stderr or "").strip()
                    if stderr:
                        for raw_line in stderr.splitlines():
                            line = raw_line.strip()
                            if not line:
                                continue
                            issue_type = "warning" if "warning:" in line else "error"
                            issues.append(
                                {
                                    "type": issue_type,
                                    "message": line,
                                    "symbol": "gxx-syntax-check",
                                }
                            )
                else:
                    proc = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "pylint",
                            tmp_path,
                            "--output-format=json",
                            "--score=n",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    output_str = (proc.stdout or "").strip()
                    if output_str:
                        try:
                            parsed = json.loads(output_str)
                            if isinstance(parsed, list):
                                issues = parsed
                        except json.JSONDecodeError:
                            issues = []

                    # If pylint cannot parse code (syntax/indentation), capture stderr as an error issue.
                    if not issues and proc.returncode != 0 and (proc.stderr or "").strip():
                        issues = [{
                            "type": "error",
                            "message": (proc.stderr or "").strip(),
                            "symbol": "pylint-runner-error",
                        }]
            except subprocess.TimeoutExpired:
                issues = [{
                    "type": "error",
                    "message": "Pylint analysis timed out.",
                    "symbol": "analysis-timeout",
                }]
            except Exception:
                issues = [{
                    "type": "error",
                    "message": "Static analysis failed unexpectedly.",
                    "symbol": "analysis-error",
                }]
            
            summary = {
                "issues": issues,
                "error_count": sum(1 for i in issues if i.get('type') == 'error'),
                "warning_count": sum(1 for i in issues if i.get('type') == 'warning'),
                "convention_count": sum(1 for i in issues if i.get('type') == 'convention'),
                "refactor_count": sum(1 for i in issues if i.get('type') == 'refactor'),
            }
            
            return summary

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

static_analyzer = StaticAnalyzer()

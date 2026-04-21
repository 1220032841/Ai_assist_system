from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Submission, ExecutionResult, StaticAnalysisResult, Rubric, Feedback
from app.services.rag.llm import llm_service
from app.services.rag.service import rag_service
import json
import subprocess
import sys
import tempfile
from typing import Any, Dict, Optional

class GradingService:
    def _normalize_output(self, text: str) -> str:
        return " ".join((text or "").strip().split())

    def _evaluate_cpp_hidden_tests(self, assignment_id: int, code: str) -> Dict[str, Any]:
        """
        Compile C++ code and run black-box hidden tests for the arithmetic assignment.
        """
        cases_by_assignment: Dict[int, list[tuple[str, str]]] = {
            1: [
                ("10 6\n", "16 4"),
                ("1 2\n", "3 -1"),
                ("-5 -8\n", "-13 3"),
            ],
        }

        cases = cases_by_assignment.get(assignment_id)
        if not cases:
            return {
                "pass_count": 0,
                "total": 0,
                "cases": [],
                "error": f"No hidden tests configured for assignment_id={assignment_id}",
            }

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                cpp_path = f"{temp_dir}/main.cpp"
                bin_path = f"{temp_dir}/main"

                with open(cpp_path, "w", encoding="utf-8") as f:
                    f.write(code)

                compile_proc = subprocess.run(
                    ["g++", "-std=c++17", cpp_path, "-O2", "-o", bin_path],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if compile_proc.returncode != 0:
                    return {
                        "pass_count": 0,
                        "total": len(cases),
                        "cases": [],
                        "error": (compile_proc.stderr or "Compile failed").strip(),
                    }

                results = []
                for test_input, expected in cases:
                    try:
                        run_proc = subprocess.run(
                            [bin_path],
                            input=test_input,
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        actual = self._normalize_output(run_proc.stdout)
                        expected_norm = self._normalize_output(expected)
                        ok = (run_proc.returncode == 0) and (actual == expected_norm)
                        results.append(
                            {
                                "input": test_input.strip(),
                                "expected": expected,
                                "actual": run_proc.stdout.strip(),
                                "ok": ok,
                                "exit_code": run_proc.returncode,
                            }
                        )
                    except subprocess.TimeoutExpired:
                        results.append(
                            {
                                "input": test_input.strip(),
                                "expected": expected,
                                "actual": "<timeout>",
                                "ok": False,
                                "exit_code": 124,
                            }
                        )

                return {
                    "pass_count": sum(1 for c in results if c["ok"]),
                    "total": len(results),
                    "cases": results,
                    "error": None,
                }
        except Exception as exc:
            return {
                "pass_count": 0,
                "total": len(cases),
                "cases": [],
                "error": f"C++ hidden tests failed: {exc}",
            }

    def _looks_like_fibonacci_assignment(self, submission: Submission) -> bool:
        assignment = submission.assignment
        text = f"{assignment.title or ''} {assignment.description or ''}".lower()
        code_text = (submission.code_content or "").lower()
        return (
            "fibonacci" in text
            or "斐波那契" in text
            or "def fibonacci(" in code_text
        )

    def _evaluate_fibonacci_hidden_tests(self, code: str) -> Dict[str, Any]:
        """
        Evaluate fibonacci logic with hidden tests.
        Returns a dict containing pass_count/total/cases/error.
        """
        harness = f"""
import json

result = {{"pass_count": 0, "total": 5, "cases": [], "error": None}}
namespace = {{}}

try:
    code = {code!r}
    exec(code, namespace, namespace)
    func = namespace.get("fibonacci")
    if not callable(func):
        result["error"] = "Function fibonacci(n) not found."
    else:
        cases = [(1, 1), (2, 1), (3, 2), (5, 5), (8, 21)]
        for n, expected in cases:
            try:
                actual = func(n)
                ok = actual == expected
            except Exception as exc:
                actual = f"<error: {{exc}}>"
                ok = False
            result["cases"].append({{"n": n, "expected": expected, "actual": actual, "ok": ok}})
        result["pass_count"] = sum(1 for c in result["cases"] if c["ok"])
except Exception as exc:
    result["error"] = f"Code execution failed: {{exc}}"

print(json.dumps(result, ensure_ascii=False))
"""

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=True, encoding="utf-8") as f:
                f.write(harness)
                f.flush()
                proc = subprocess.run(
                    [sys.executable, f.name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            output = (proc.stdout or "").strip()
            if proc.returncode != 0 or not output:
                return {
                    "pass_count": 0,
                    "total": 5,
                    "cases": [],
                    "error": (proc.stderr or "Hidden test runner failed").strip(),
                }
            return json.loads(output)
        except subprocess.TimeoutExpired:
            return {
                "pass_count": 0,
                "total": 5,
                "cases": [],
                "error": "Hidden tests timed out.",
            }
        except Exception as exc:
            return {
                "pass_count": 0,
                "total": 5,
                "cases": [],
                "error": f"Hidden tests failed: {exc}",
            }

    def _looks_like_linked_list_assignment(self, submission: Submission) -> bool:
        assignment = submission.assignment
        text = f"{assignment.title or ''} {assignment.description or ''}".lower()
        code_text = (submission.code_content or "").lower()
        return (
            "linked list" in text
            or "链表" in text
            or "reverse_linked_list" in text
            or "def reverse_linked_list(" in code_text
        )

    def _evaluate_linked_list_hidden_tests(self, code: str) -> Dict[str, Any]:
        """
        Evaluate reverse_linked_list(head) with hidden test cases.
        Returns a dict containing pass_count/total/cases/error.
        """
        harness = f"""
import json

result = {{"pass_count": 0, "total": 4, "cases": [], "error": None}}
namespace = {{}}

def to_list(head, max_nodes=100):
    values = []
    steps = 0
    cur = head
    while cur is not None and steps < max_nodes:
        values.append(getattr(cur, "val", None))
        cur = getattr(cur, "next", None)
        steps += 1
    if steps >= max_nodes:
        values.append("<cycle>")
    return values

try:
    code = {code!r}
    exec(code, namespace, namespace)
    func = namespace.get("reverse_linked_list")
    NodeCls = namespace.get("ListNode")

    if not callable(func):
        result["error"] = "Function reverse_linked_list(head) not found."
    else:
        if not callable(NodeCls):
            class ListNode:
                def __init__(self, val=0, next=None):
                    self.val = val
                    self.next = next
            NodeCls = ListNode

        def build_list(values):
            head = None
            tail = None
            for v in values:
                node = NodeCls(v)
                if head is None:
                    head = node
                    tail = node
                else:
                    tail.next = node
                    tail = node
            return head

        cases = [
            ([], []),
            ([1], [1]),
            ([1, 2], [2, 1]),
            ([1, 2, 3, 4], [4, 3, 2, 1]),
        ]
        for data, expected in cases:
            try:
                head = build_list(data)
                reversed_head = func(head)
                actual = to_list(reversed_head)
                ok = actual == expected
            except Exception as exc:
                actual = [f"<error: {{exc}}>" ]
                ok = False

            result["cases"].append({{
                "input": data,
                "expected": expected,
                "actual": actual,
                "ok": ok,
            }})

        result["pass_count"] = sum(1 for c in result["cases"] if c["ok"])
except Exception as exc:
    result["error"] = f"Code execution failed: {{exc}}"

print(json.dumps(result, ensure_ascii=False))
"""

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=True, encoding="utf-8") as f:
                f.write(harness)
                f.flush()
                proc = subprocess.run(
                    [sys.executable, f.name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            output = (proc.stdout or "").strip()
            if proc.returncode != 0 or not output:
                return {
                    "pass_count": 0,
                    "total": 4,
                    "cases": [],
                    "error": (proc.stderr or "Hidden test runner failed").strip(),
                }
            return json.loads(output)
        except subprocess.TimeoutExpired:
            return {
                "pass_count": 0,
                "total": 4,
                "cases": [],
                "error": "Hidden tests timed out.",
            }
        except Exception as exc:
            return {
                "pass_count": 0,
                "total": 4,
                "cases": [],
                "error": f"Hidden tests failed: {exc}",
            }

    def _score_submission(self, submission: Submission) -> Dict[str, Any]:
        execution_result = submission.execution_result

        if not execution_result or execution_result.exit_code != 0:
            return {
                "final_score": 0,
                "breakdown": {
                    "execution": "failed",
                    "exam_score": 0,
                    "reason": "Runtime/compile failed before grading logic.",
                },
            }

        # Binary exam-score policy:
        # - Final score only judges correctness of assignment objective.
        # - Static analysis is informational and never reduces final score.
        if self._looks_like_fibonacci_assignment(submission) and submission.language == "python":
            hidden = self._evaluate_fibonacci_hidden_tests(submission.code_content)
            if hidden.get("error"):
                return {
                    "final_score": 0,
                    "breakdown": {
                        "execution": "ok",
                        "exam_score": 0,
                        "hidden_tests": hidden,
                        "reason": hidden["error"],
                    },
                }

            pass_count = hidden.get("pass_count", 0)
            total = hidden.get("total", 5)
            final_score = 100 if pass_count == total else 0
            return {
                "final_score": final_score,
                "breakdown": {
                    "execution": "ok",
                    "exam_score": final_score,
                    "hidden_tests": hidden,
                    "reason": "All hidden tests passed." if final_score == 100 else "Hidden tests not fully passed.",
                },
            }

        if self._looks_like_linked_list_assignment(submission) and submission.language == "python":
            hidden = self._evaluate_linked_list_hidden_tests(submission.code_content)
            if hidden.get("error"):
                return {
                    "final_score": 0,
                    "breakdown": {
                        "execution": "ok",
                        "exam_score": 0,
                        "hidden_tests": hidden,
                        "reason": hidden["error"],
                    },
                }

            pass_count = hidden.get("pass_count", 0)
            total = hidden.get("total", 4)
            final_score = 100 if pass_count == total else 0
            return {
                "final_score": final_score,
                "breakdown": {
                    "execution": "ok",
                    "exam_score": final_score,
                    "hidden_tests": hidden,
                    "reason": "All hidden tests passed." if final_score == 100 else "Hidden tests not fully passed.",
                },
            }

        if submission.language == "cpp" and submission.assignment_id == 1:
            hidden = self._evaluate_cpp_hidden_tests(submission.assignment_id, submission.code_content)
            if hidden.get("error"):
                return {
                    "final_score": 0,
                    "breakdown": {
                        "execution": "ok",
                        "exam_score": 0,
                        "hidden_tests": hidden,
                        "reason": hidden["error"],
                    },
                }

            pass_count = hidden.get("pass_count", 0)
            total = hidden.get("total", 0)
            final_score = 100 if total > 0 and pass_count == total else 0
            return {
                "final_score": final_score,
                "breakdown": {
                    "execution": "ok",
                    "exam_score": final_score,
                    "hidden_tests": hidden,
                    "reason": "All hidden tests passed." if final_score == 100 else "Hidden tests not fully passed.",
                },
            }

        final_score = 100
        return {
            "final_score": final_score,
            "breakdown": {
                "execution": "ok",
                "exam_score": 100,
                "reason": "Fallback full-credit policy: execution succeeded.",
            },
        }

    async def grade_submission(self, db: AsyncSession, submission: Submission):
        """
        Orchestrates the grading process.
        """
        # 1. Fetch related data
        execution_result = submission.execution_result
        static_analysis = submission.static_analysis
        assignment = submission.assignment
        rubric = assignment.rubric
        
        # 2. Retrieve context for RAG
        # Assuming we search based on assignment title or description + code keywords
        query = f"{assignment.title} {assignment.description}"
        retrieved_docs = await rag_service.retrieve(db, query)
        
        # 3. Generate Feedback via LLM
        feedback_text = await llm_service.generate_feedback(
            submission, execution_result, static_analysis, retrieved_docs
        )
        
        # 4. Calculate deterministic score with hidden tests.
        score_result = self._score_submission(submission)
        final_score = score_result["final_score"]
        breakdown = score_result["breakdown"]
             
        # 5. Save Feedback
        feedback = Feedback(
            submission_id=submission.id,
            content=feedback_text,
            final_score=final_score,
            citations=[d.title for d in retrieved_docs],
            grade_breakdown=breakdown,
        )
        db.add(feedback)
        await db.commit()
        
        return feedback

grading_service = GradingService()

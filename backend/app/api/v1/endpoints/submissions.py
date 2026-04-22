from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from textwrap import dedent
import ast
import logging
import re
from typing import Optional, Tuple

from app.api import deps
from app.db.session import get_db
from app.db.models import Assignment, Submission, User, ExecutionResult, StaticAnalysisResult, Feedback
from app.schemas import submission as submission_schema
from app.services.execution.runner import execution_service

router = APIRouter()
logger = logging.getLogger(__name__)


async def _delete_submission_related_rows(db: AsyncSession, submission_id: int) -> None:
    await db.execute(delete(ExecutionResult).where(ExecutionResult.submission_id == submission_id))
    await db.execute(delete(StaticAnalysisResult).where(StaticAnalysisResult.submission_id == submission_id))
    await db.execute(delete(Feedback).where(Feedback.submission_id == submission_id))
    await db.execute(delete(Submission).where(Submission.id == submission_id))


def _normalize_assignment_language(language: Optional[str]) -> str:
    normalized = (language or "cpp").strip().lower()
    return "python" if normalized == "python" else "cpp"


def _default_assignment_starter_code(language: str) -> Optional[str]:
    if language == "python":
        return (
            "def solve():\n"
            "    # TODO: 在这里实现你的逻辑\n"
            "    pass\n\n"
            "if __name__ == '__main__':\n"
            "    solve()\n"
        )

    if language == "cpp":
        return (
            "#include <iostream>\n"
            "using namespace std;\n\n"
            "int main() {\n"
            "    // TODO: 在这里实现你的逻辑\n"
            "    cout << \"hello world\" << endl;\n"
            "    return 0;\n"
            "}\n"
        )

    return None


def _get_assignment_starter_code(assignment: Assignment, language: str) -> Optional[str]:
    starter_code = (assignment.starter_code or "").rstrip() if assignment else ""
    if starter_code:
        return starter_code
    return _default_assignment_starter_code(language)


def _filter_starter_template_issues(
    analysis_summary: dict,
    submitted_code: str,
    starter_code: str,
) -> Tuple[dict, int]:
    """
    Remove pylint issues produced by unchanged starter-template lines.
    Returns (filtered_summary, student_non_template_line_count).
    """
    def _canonical_line(line: str) -> str:
        stripped = line.strip()
        if not stripped:
            return ""
        if "#" in stripped:
            stripped = stripped.split("#", 1)[0].rstrip()
        return re.sub(r"\s+", " ", stripped)

    submitted_lines = submitted_code.splitlines()
    starter_lines = _normalize_python_code(starter_code).splitlines()

    template_line_nums: set[int] = set()
    upto = min(len(submitted_lines), len(starter_lines))
    for i in range(upto):
        if _canonical_line(submitted_lines[i]) == _canonical_line(starter_lines[i]):
            template_line_nums.add(i + 1)

    student_non_template_line_count = 0
    for idx, line in enumerate(submitted_lines, start=1):
        if line.strip() and idx not in template_line_nums:
            student_non_template_line_count += 1

    raw_issues = analysis_summary.get("issues", []) if isinstance(analysis_summary, dict) else []
    filtered_issues = []
    for issue in raw_issues:
        if not isinstance(issue, dict):
            continue
        line_no = issue.get("line")
        if isinstance(line_no, int) and line_no in template_line_nums:
            continue
        filtered_issues.append(issue)

    filtered_summary = {
        "issues": filtered_issues,
        "error_count": sum(1 for i in filtered_issues if i.get("type") == "error"),
        "warning_count": sum(1 for i in filtered_issues if i.get("type") == "warning"),
        "convention_count": sum(1 for i in filtered_issues if i.get("type") == "convention"),
        "refactor_count": sum(1 for i in filtered_issues if i.get("type") == "refactor"),
    }
    return filtered_summary, student_non_template_line_count


def _normalize_cpp_code(code: str) -> str:
    return (
        (code or "")
        .replace("\u3000", " ")
        .replace("\xa0", " ")
        .expandtabs(4)
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip("\n\r")
    )


def _normalize_submission_code(code: str, language: str) -> str:
    if language == "python":
        return _normalize_python_code(code)
    if language == "cpp":
        return _normalize_cpp_code(code)
    return (code or "").strip()


def _canonical_line_for_compare(line: str, language: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""

    if language == "python":
        if "#" in stripped:
            stripped = stripped.split("#", 1)[0].rstrip()
    elif language == "cpp":
        if "//" in stripped:
            stripped = stripped.split("//", 1)[0].rstrip()

    return re.sub(r"\s+", " ", stripped).strip()


def _extract_non_template_code(submitted_code: str, starter_code: str, language: str) -> Tuple[str, int, bool]:
    submitted_norm = _normalize_submission_code(submitted_code, language)
    starter_norm = _normalize_submission_code(starter_code, language)

    submitted_lines = submitted_norm.splitlines()
    starter_lines = starter_norm.splitlines()

    template_line_nums: set[int] = set()
    upto = min(len(submitted_lines), len(starter_lines))
    for i in range(upto):
        if _canonical_line_for_compare(submitted_lines[i], language) == _canonical_line_for_compare(starter_lines[i], language):
            template_line_nums.add(i + 1)

    non_template_lines: list[str] = []
    for idx, line in enumerate(submitted_lines, start=1):
        if line.strip() and idx not in template_line_nums:
            non_template_lines.append(line)

    submitted_sig = [
        _canonical_line_for_compare(line, language)
        for line in submitted_norm.splitlines()
        if _canonical_line_for_compare(line, language)
    ]
    starter_sig = [
        _canonical_line_for_compare(line, language)
        for line in starter_norm.splitlines()
        if _canonical_line_for_compare(line, language)
    ]
    template_only = submitted_sig == starter_sig

    return "\n".join(non_template_lines), len(non_template_lines), template_only


def _is_template_only_submission(submitted_code: str, starter_code: str, language: str) -> bool:
    submitted_norm = _normalize_submission_code(submitted_code, language).strip()
    starter_norm = _normalize_submission_code(starter_code, language).strip()
    if submitted_norm == starter_norm:
        return True

    submitted_sig = [
        _canonical_line_for_compare(line, language)
        for line in submitted_norm.splitlines()
        if _canonical_line_for_compare(line, language)
    ]
    starter_sig = [
        _canonical_line_for_compare(line, language)
        for line in starter_norm.splitlines()
        if _canonical_line_for_compare(line, language)
    ]
    return submitted_sig == starter_sig


def _is_placeholder_linked_list_solution(code: str) -> bool:
    """
    Detect empty/skeleton reverse_linked_list implementations and force zero static score.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    target = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "reverse_linked_list":
            target = node
            break
    if not target:
        return False

    if not target.body:
        return True

    meaningful = False
    for stmt in target.body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
            continue
        if isinstance(stmt, ast.Return) and (
            stmt.value is None
            or (isinstance(stmt.value, ast.Constant) and stmt.value.value is None)
        ):
            continue
        if (
            isinstance(stmt, ast.Raise)
            and isinstance(stmt.exc, ast.Call)
            and isinstance(stmt.exc.func, ast.Name)
            and stmt.exc.func.id == "NotImplementedError"
        ):
            continue
        meaningful = True
        break

    return not meaningful


def _normalize_python_code(code: str) -> str:
    """
    Normalize pasted code and repair one common formatting issue:
    function body lines accidentally aligned with `def` line.
    """
    def _syntax_ok(src: str) -> bool:
        try:
            compile(src, "<submission>", "exec")
            return True
        except SyntaxError:
            return False

    def _repair_flat_function_body(src: str) -> str:
        lines = src.split("\n") if src else []
        if not lines:
            return src

        for i in range(len(lines) - 1):
            line = lines[i]
            if not re.match(r"^\s*def\s+\w+\s*\(.*\)\s*:\s*$", line):
                continue

            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines):
                continue

            # If first body line is not indented, treat this as accidental flattening and fix it.
            if lines[j].lstrip() == lines[j]:
                k = j
                while k < len(lines):
                    if not lines[k].strip():
                        k += 1
                        continue
                    if re.match(r"^(def|class)\s+", lines[k]) and k != j:
                        break
                    lines[k] = "    " + lines[k]
                    k += 1

        return "\n".join(lines)

    def _heuristic_reindent(src: str) -> str:
        """
        Best-effort indentation rebuild for pasted code with mixed/invalid indent.
        This is intentionally conservative and only used as last fallback.
        """
        lines = src.split("\n")
        if not lines:
            return src

        rebuilt: list[str] = []
        indent_level = 0
        dedent_prefix = ("elif ", "else:", "except", "finally:")

        for raw in lines:
            stripped = raw.strip()
            if not stripped:
                rebuilt.append("")
                continue

            if any(stripped.startswith(p) for p in dedent_prefix):
                indent_level = max(0, indent_level - 1)

            rebuilt.append(("    " * indent_level) + stripped)

            # Open a new block after ':' (excluding comments-only lines).
            if stripped.endswith(":") and not stripped.startswith("#"):
                indent_level += 1

        return "\n".join(rebuilt)

    preprocessed = (
        code.replace("\u3000", " ")
        .replace("\xa0", " ")
        .expandtabs(4)
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    normalized = dedent(preprocessed).strip("\n\r")

    if _syntax_ok(normalized):
        return normalized

    repaired = _repair_flat_function_body(normalized)
    if _syntax_ok(repaired):
        return repaired

    fallback = _heuristic_reindent(repaired)
    if _syntax_ok(fallback):
        return fallback

    # If all repair attempts fail, return the normalized text for transparent error reporting.
    return repaired


def _is_placeholder_fibonacci_solution(code: str) -> bool:
    """
    Detect empty/skeleton fibonacci implementations and force zero static score.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    target = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "fibonacci":
            target = node
            break
    if not target:
        return False

    if not target.body:
        return True

    meaningful = False
    for stmt in target.body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
            continue
        if isinstance(stmt, ast.Return) and (
            stmt.value is None
            or (isinstance(stmt.value, ast.Constant) and stmt.value.value is None)
        ):
            continue
        if (
            isinstance(stmt, ast.Raise)
            and isinstance(stmt.exc, ast.Call)
            and isinstance(stmt.exc.func, ast.Name)
            and stmt.exc.func.id == "NotImplementedError"
        ):
            continue
        meaningful = True
        break

    return not meaningful


def _score_cpp_static_analysis(code: str, analysis_summary: dict, assignment_id: int) -> int:
    """
    Logic-first static scoring for C++ submissions.
    Syntax/compile issues only apply a capped penalty, so students can still
    receive meaningful static scores when algorithmic intent is clear.
    """
    normalized = (code or "").lower()
    non_empty_lines = [line for line in (code or "").splitlines() if line.strip()]

    logic_points = 0
    if "#include" in normalized:
        logic_points += 8
    if "int main" in normalized:
        logic_points += 12
    if "while" in normalized or "for" in normalized:
        logic_points += 8
    if "return" in normalized:
        logic_points += 4

    if assignment_id == 1:
        if "cin" in normalized:
            logic_points += 10
        if "cout" in normalized:
            logic_points += 12
        if "+" in normalized:
            logic_points += 12
        if "-" in normalized:
            logic_points += 12

    logic_points = min(logic_points, 70)
    base_score = 25 + logic_points

    error_count = int(analysis_summary.get("error_count", 0) or 0)
    warning_count = int(analysis_summary.get("warning_count", 0) or 0)
    convention_count = int(analysis_summary.get("convention_count", 0) or 0)

    # Capped deduction keeps syntax mistakes secondary to algorithmic intent.
    penalty = min(18, error_count * 1.5 + warning_count * 0.75 + convention_count * 0.3)
    score = round(base_score - penalty)

    if logic_points >= 40 and score < 60:
        score = 60
    if logic_points >= 55 and score < 70:
        score = 70

    if not non_empty_lines:
        return 0

    return max(0, min(100, score))

@router.post("/", response_model=submission_schema.SubmissionDetail)
async def create_submission(
    *,
    db: AsyncSession = Depends(get_db),
    submission_in: submission_schema.SubmissionCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Submit code for an assignment.
    """
    # 1. Validate assignment and calculate version
    assignment_stmt = select(Assignment).where(Assignment.id == submission_in.assignment_id)
    assignment_result = await db.execute(assignment_stmt)
    assignment = assignment_result.scalars().first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    expected_language = _normalize_assignment_language(getattr(assignment, "language", None))
    submitted_language = _normalize_assignment_language(submission_in.language)
    if submitted_language != expected_language:
        raise HTTPException(status_code=400, detail=f"This assignment only accepts {expected_language} submissions")

    version_stmt = select(func.max(Submission.version)).where(
        Submission.assignment_id == submission_in.assignment_id,
        Submission.student_id == current_user.id,
    )
    version_result = await db.execute(version_stmt)
    next_version = (version_result.scalar() or 0) + 1

    # Normalize common pasted indentation to avoid false "unexpected indent" errors.
    normalized_code = _normalize_submission_code(submission_in.code_content, expected_language)
    if not normalized_code.strip():
        raise HTTPException(status_code=400, detail="Code content cannot be empty")
    
    submission = Submission(
        assignment_id=submission_in.assignment_id,
        student_id=current_user.id,
        code_content=normalized_code,
        language=expected_language,
        version=next_version,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    
    # 2. Trigger Execution (Async in background ideally, but sync for now)
    stdout, stderr, exit_code = execution_service.run_code(submission.code_content, submission.language)
    
    execution_result = ExecutionResult(
        submission_id=submission.id,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code
    )
    db.add(execution_result)
    
    # 3. Trigger Static Analysis
    from app.services.analysis.static_analyzer import static_analyzer
    from app.db.models import StaticAnalysisResult
    
    analysis_summary = static_analyzer.analyze(submission.code_content, submission.language)

    starter_code = _get_assignment_starter_code(assignment, submission.language)
    student_non_template_line_count: Optional[int] = None
    template_only_submission = False
    cpp_non_template_code = normalized_code
    if starter_code:
        non_template_code, student_non_template_line_count, template_only_submission = _extract_non_template_code(
            submitted_code=normalized_code,
            starter_code=starter_code,
            language=submission.language,
        )
        if submission.language == "cpp":
            cpp_non_template_code = non_template_code

        if submission.language == "python":
            analysis_summary, _ = _filter_starter_template_issues(
                analysis_summary=analysis_summary,
                submitted_code=normalized_code,
                starter_code=starter_code,
            )

        template_only_submission = _is_template_only_submission(
            submitted_code=normalized_code,
            starter_code=starter_code,
            language=submission.language,
        )

    if student_non_template_line_count is None:
        student_non_template_line_count = len([line for line in normalized_code.splitlines() if line.strip()])

    blank_submission_reason: Optional[str] = None
    if template_only_submission:
        blank_submission_reason = "检测到提交内容与题目样例模板基本一致（白卷/模板提交）"
    elif student_non_template_line_count == 0:
        blank_submission_reason = "未检测到有效的学生新增代码（白卷/模板提交）"

    # Calculate a score from 0-100 based on analysis severity.
    # For teaching: prioritize algorithmic intent, keep syntax penalties secondary.
    base_score = 100
    issues_list = analysis_summary.get('issues', []) if isinstance(analysis_summary, dict) else []
    has_syntax_error = any(
        i.get('symbol') == 'syntax-error' or i.get('message-id') == 'E0001'
        for i in issues_list
        if isinstance(i, dict)
    )

    if template_only_submission:
        # Template/sample-only submission should not receive static points.
        base_score = 0
    elif student_non_template_line_count == 0:
        # If student only submitted the provided starter template, static score should be zero.
        base_score = 0
    elif submission.language == "cpp":
        base_score = _score_cpp_static_analysis(
            code=cpp_non_template_code,
            analysis_summary=analysis_summary,
            assignment_id=submission.assignment_id,
        )
    elif has_syntax_error:
        # Syntax mistakes should not completely erase logic-oriented static score.
        non_empty_lines = [line for line in normalized_code.splitlines() if line.strip()]
        base_score = 50 if len(non_empty_lines) >= 10 else 35
    else:
        base_score -= (analysis_summary.get('error_count', 0) * 12)
        base_score -= (analysis_summary.get('warning_count', 0) * 3)
        base_score -= (analysis_summary.get('convention_count', 0) * 1)

    base_score = max(0, base_score)

    if not isinstance(analysis_summary, dict):
        analysis_summary = {
            "issues": [],
            "error_count": 0,
            "warning_count": 0,
            "convention_count": 0,
            "refactor_count": 0,
        }

    issues_for_display = analysis_summary.get("issues", [])
    if not isinstance(issues_for_display, list):
        issues_for_display = []

    blank_submission_detected = blank_submission_reason is not None
    if blank_submission_detected and not any(
        isinstance(i, dict) and i.get("symbol") == "blank-submission"
        for i in issues_for_display
    ):
        issues_for_display.insert(
            0,
            {
                "type": "warning",
                "symbol": "blank-submission",
                "message": blank_submission_reason,
            },
        )

    analysis_summary["issues"] = issues_for_display
    analysis_summary["blank_submission_detected"] = blank_submission_detected
    analysis_summary["blank_submission_reason"] = blank_submission_reason
    analysis_summary["starter_template_matched"] = bool(template_only_submission)
    analysis_summary["student_non_template_line_count"] = int(student_non_template_line_count)
    
    static_result = StaticAnalysisResult(
        submission_id=submission.id,
        issues=analysis_summary,
        score=base_score
    )
    db.add(static_result)
    await db.commit() # Commit execution and analysis first
    
    # 4. Trigger Grading (RAG + LLM)
    from app.services.grading.grader import grading_service
    stmt = select(Submission).where(Submission.id == submission.id)
    stmt = stmt.options(
        selectinload(Submission.execution_result),
        selectinload(Submission.static_analysis),
        selectinload(Submission.feedback),
        selectinload(Submission.assignment).selectinload(Assignment.rubric),
    )
    result = await db.execute(stmt)
    submission_loaded = result.scalars().first()

    try:
        await grading_service.grade_submission(db, submission_loaded)
    except Exception as exc:
        logger.exception("Grading failed for submission_id=%s", submission.id)
        await db.rollback()

        score_result = grading_service._score_submission(submission_loaded)
        fallback_feedback = Feedback(
            submission_id=submission.id,
            content=(
                "AI 反馈暂时生成失败，但本次提交已保存。\n\n"
                f"系统错误信息: {str(exc)}\n\n"
                "你可以稍后刷新结果页，或重新提交一次以再次触发反馈生成。"
            ),
            citations=[],
            grade_breakdown=score_result["breakdown"],
            final_score=score_result["final_score"],
        )
        db.add(fallback_feedback)
        await db.commit()

    final_stmt = (
        select(Submission)
        .options(
            selectinload(Submission.execution_result),
            selectinload(Submission.static_analysis),
            selectinload(Submission.feedback),
        )
        .where(Submission.id == submission.id)
    )
    final_result = await db.execute(final_stmt)
    return final_result.scalars().first()

@router.get("/", response_model=List[submission_schema.Submission])
async def read_submissions(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve submissions.
    """
    if current_user.role == "student":
        result = await db.execute(
            select(Submission)
            .options(selectinload(Submission.execution_result))
            .where(Submission.student_id == current_user.id)
            .order_by(Submission.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
    else:
        result = await db.execute(
            select(Submission)
            .options(selectinload(Submission.execution_result))
            .order_by(Submission.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
    return result.scalars().all()


@router.delete("/{submission_id}", response_model=submission_schema.SubmissionDeleteResponse)
async def delete_submission(
    *,
    db: AsyncSession = Depends(get_db),
    submission_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    stmt = select(Submission).where(Submission.id == submission_id)
    result = await db.execute(stmt)
    submission = result.scalars().first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if current_user.role == "student" and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    await _delete_submission_related_rows(db, submission_id)
    await db.commit()
    return {"deleted_count": 1}


@router.post("/bulk-delete", response_model=submission_schema.SubmissionDeleteResponse)
async def bulk_delete_submissions(
    *,
    db: AsyncSession = Depends(get_db),
    payload: submission_schema.SubmissionBulkDeleteRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    ids = [i for i in payload.submission_ids if isinstance(i, int)]
    if not ids:
        return {"deleted_count": 0}

    query = select(Submission).where(Submission.id.in_(ids))
    if current_user.role == "student":
        query = query.where(Submission.student_id == current_user.id)

    result = await db.execute(query)
    submissions = result.scalars().all()

    for submission in submissions:
        await _delete_submission_related_rows(db, submission.id)

    await db.commit()
    return {"deleted_count": len(submissions)}


@router.delete("/", response_model=submission_schema.SubmissionDeleteResponse)
async def delete_all_submissions(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    query = select(Submission)
    if current_user.role == "student":
        query = query.where(Submission.student_id == current_user.id)

    result = await db.execute(query)
    submissions = result.scalars().all()

    for submission in submissions:
        await _delete_submission_related_rows(db, submission.id)

    await db.commit()
    return {"deleted_count": len(submissions)}


@router.get("/{submission_id}", response_model=submission_schema.SubmissionDetail)
async def read_submission(
    *,
    db: AsyncSession = Depends(get_db),
    submission_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get submission by ID.
    """
    stmt = select(Submission).options(
        selectinload(Submission.execution_result),
        selectinload(Submission.static_analysis),
        selectinload(Submission.feedback),
    ).where(Submission.id == submission_id)
    
    result = await db.execute(stmt)
    submission = result.scalars().first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    if current_user.role == "student" and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    return submission


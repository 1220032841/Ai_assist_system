from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.models import Assignment, Course, ExecutionResult, Feedback, StaticAnalysisResult, Submission, User
from app.db.session import get_db
from app.schemas import assignment as assignment_schema

router = APIRouter()

SUPPORTED_ASSIGNMENT_LANGUAGES = {"cpp", "python"}


def _normalize_assignment_language(language: Optional[str]) -> str:
    normalized = (language or "cpp").strip().lower()
    if normalized not in SUPPORTED_ASSIGNMENT_LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported assignment language")
    return normalized


def _default_assignment_starter_code(language: str) -> str:
    if language == "python":
        return (
            "def solve():\n"
            "    # TODO: 在这里实现你的逻辑\n"
            "    pass\n\n"
            "if __name__ == '__main__':\n"
            "    solve()\n"
        )

    return (
        "#include <iostream>\n"
        "using namespace std;\n\n"
        "int main() {\n"
        "    // TODO: 在这里实现你的逻辑\n"
        "    cout << \"hello world\" << endl;\n"
        "    return 0;\n"
        "}\n"
    )


@router.get("/", response_model=List[assignment_schema.Assignment])
async def read_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve all assignments for the current course set.
    """
    result = await db.execute(select(Assignment).order_by(Assignment.id.asc()))
    return result.scalars().all()


@router.get("/{assignment_id}", response_model=assignment_schema.Assignment)
async def read_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve a single assignment.
    """
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalars().first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.post("/", response_model=assignment_schema.Assignment)
async def create_assignment(
    *,
    db: AsyncSession = Depends(get_db),
    payload: assignment_schema.AssignmentCreate,
    current_user: User = Depends(deps.get_current_teacher),
) -> Any:
    """
    Teacher action: create a new assignment.
    """
    title = (payload.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Assignment title cannot be empty")

    language = _normalize_assignment_language(payload.language)
    starter_code = (payload.starter_code or "").rstrip()
    if not starter_code:
        starter_code = _default_assignment_starter_code(language)

    course = None
    if payload.course_id is not None:
        course_result = await db.execute(select(Course).where(Course.id == payload.course_id))
        course = course_result.scalars().first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        if current_user.role != "admin" and course.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed to create assignment for this course")
    else:
        course_result = await db.execute(
            select(Course)
            .where(Course.instructor_id == current_user.id)
            .order_by(Course.id.asc())
        )
        course = course_result.scalars().first()

        if not course:
            course = Course(
                title=f"{current_user.full_name or current_user.email} Course",
                description="Auto-created default course",
                instructor_id=current_user.id,
            )
            db.add(course)
            await db.flush()

    assignment = Assignment(
        course_id=course.id,
        title=title,
        description=(payload.description or "").strip() or None,
        language=language,
        starter_code=starter_code,
        example_input=(payload.example_input or "").strip() or None,
        example_output=(payload.example_output or "").strip() or None,
        due_date=payload.due_date,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", response_model=assignment_schema.AssignmentDeleteResponse)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
) -> Any:
    assignment_result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = assignment_result.scalars().first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    course_result = await db.execute(select(Course).where(Course.id == assignment.course_id))
    course = course_result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this assignment")

    submission_ids = (
        await db.execute(select(Submission.id).where(Submission.assignment_id == assignment_id))
    ).scalars().all()

    if submission_ids:
        await db.execute(delete(ExecutionResult).where(ExecutionResult.submission_id.in_(submission_ids)))
        await db.execute(delete(StaticAnalysisResult).where(StaticAnalysisResult.submission_id.in_(submission_ids)))
        await db.execute(delete(Feedback).where(Feedback.submission_id.in_(submission_ids)))
        await db.execute(delete(Submission).where(Submission.id.in_(submission_ids)))

    await db.execute(delete(Assignment).where(Assignment.id == assignment_id))
    await db.commit()
    return {"deleted_id": assignment_id}

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.models import Assignment, Course, User
from app.db.session import get_db
from app.schemas import assignment as assignment_schema

router = APIRouter()


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
        due_date=payload.due_date,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment

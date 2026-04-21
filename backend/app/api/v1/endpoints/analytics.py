from typing import Any, List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.api import deps
from app.db.session import get_db
from app.db.models import Submission, User, Feedback, ExecutionResult, Assignment

router = APIRouter()


@router.get("/gradebook")
async def get_gradebook(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
) -> List[Dict[str, Any]]:
    """
    Teacher gradebook view:
    one latest row per (student, assignment) with final/static score.
    """
    students_result = await db.execute(
        select(User).where(User.role == "student").order_by(User.id.asc())
    )
    students = students_result.scalars().all()

    assignments_result = await db.execute(
        select(Assignment).order_by(Assignment.id.asc())
    )
    assignments = assignments_result.scalars().all()

    submissions_result = await db.execute(
        select(Submission)
        .options(
            selectinload(Submission.feedback),
            selectinload(Submission.static_analysis),
            selectinload(Submission.execution_result),
        )
        .order_by(Submission.created_at.desc())
    )
    submissions = submissions_result.scalars().all()

    latest_map: dict[tuple[int, int], Submission] = {}
    for submission in submissions:
        key = (submission.student_id, submission.assignment_id)
        if key not in latest_map:
            latest_map[key] = submission

    rows: List[Dict[str, Any]] = []
    for student in students:
        for assignment in assignments:
            sub = latest_map.get((student.id, assignment.id))
            if not sub:
                status = "not_submitted"
            elif not sub.execution_result:
                status = "pending"
            else:
                status = "completed" if sub.execution_result.exit_code == 0 else "failed"
            rows.append(
                {
                    "student_id": student.id,
                    "student_email": student.email,
                    "student_name": student.full_name,
                    "class_name": student.class_name,
                    "assignment_id": assignment.id,
                    "assignment_title": assignment.title,
                    "final_score": sub.feedback.final_score if sub and sub.feedback else None,
                    "static_score": sub.static_analysis.score if sub and sub.static_analysis else None,
                    "status": status,
                    "submission_id": sub.id if sub else None,
                    "submitted_at": sub.created_at if sub else None,
                }
            )

    return rows


@router.get("/student-detail/{student_id}")
async def get_student_detail(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
) -> Dict[str, Any]:
    """
    Teacher view: student profile and submission history.
    """
    student_res = await db.execute(
        select(User).where(User.id == student_id, User.role == "student")
    )
    student = student_res.scalars().first()
    if not student:
        return {"student": None, "submissions": []}

    submissions_res = await db.execute(
        select(Submission)
        .options(
            selectinload(Submission.assignment),
            selectinload(Submission.execution_result),
            selectinload(Submission.static_analysis),
            selectinload(Submission.feedback),
        )
        .where(Submission.student_id == student_id)
        .order_by(Submission.created_at.desc())
    )
    submissions = submissions_res.scalars().all()

    rows: List[Dict[str, Any]] = []
    for sub in submissions:
        if not sub.execution_result:
            status = "pending"
        else:
            status = "completed" if sub.execution_result.exit_code == 0 else "failed"

        rows.append(
            {
                "submission_id": sub.id,
                "assignment_id": sub.assignment_id,
                "assignment_title": sub.assignment.title if sub.assignment else None,
                "version": sub.version,
                "language": sub.language,
                "status": status,
                "final_score": sub.feedback.final_score if sub.feedback else None,
                "static_score": sub.static_analysis.score if sub.static_analysis else None,
                "feedback_content": sub.feedback.content if sub.feedback else None,
                "grade_breakdown": sub.feedback.grade_breakdown if sub.feedback else None,
                "feedback_created_at": sub.feedback.created_at if sub.feedback else None,
                "created_at": sub.created_at,
            }
        )

    return {
        "student": {
            "id": student.id,
            "email": student.email,
            "full_name": student.full_name,
            "class_name": student.class_name,
            "is_active": student.is_active,
            "role": student.role,
        },
        "submissions": rows,
    }

@router.get("/class-performance/{course_id}")
async def get_class_performance(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser), # Admin/Instructor only
) -> Dict[str, Any]:
    """
    Get aggregated performance metrics for a course.
    """
    # Average score per assignment
    # This query is a bit complex for async sqlalchemy without explicit join syntax sometimes,
    # let's do it simply.
    
    # Get all assignments for course
    result = await db.execute(select(Assignment).where(Assignment.course_id == course_id))
    assignments = result.scalars().all()
    
    performance_data = []
    
    for assignment in assignments:
        # Get all feedbacks for this assignment's submissions
        # Join Feedback -> Submission -> Assignment
        stmt = (
            select(func.avg(Feedback.final_score))
            .join(Submission, Feedback.submission_id == Submission.id)
            .where(Submission.assignment_id == assignment.id)
        )
        avg_score_res = await db.execute(stmt)
        avg_score = avg_score_res.scalar() or 0.0
        
        performance_data.append({
            "assignment_id": assignment.id,
            "title": assignment.title,
            "average_score": round(avg_score, 2)
        })
        
    return {
        "course_id": course_id,
        "assignments": performance_data
    }

@router.get("/error-clusters/{assignment_id}")
async def get_error_clusters(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> List[Dict[str, Any]]:
    """
    Identify common errors for an assignment.
    """
    # Group by exit code or stderr content (simplified)
    stmt = (
        select(ExecutionResult.exit_code, func.count(ExecutionResult.id))
        .join(Submission, ExecutionResult.submission_id == Submission.id)
        .where(Submission.assignment_id == assignment_id)
        .group_by(ExecutionResult.exit_code)
    )
    
    result = await db.execute(stmt)
    clusters = result.all()
    
    return [
        {"exit_code": row[0], "count": row[1], "description": "Runtime Error" if row[0] != 0 else "Success"}
        for row in clusters
    ]

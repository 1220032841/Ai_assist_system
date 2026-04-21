from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.api import deps
from app.core import security
from app.db.session import get_db
from app.db.models import User, Submission, ExecutionResult, StaticAnalysisResult, Feedback, Enrollment, ClassGroup
from app.schemas import user as user_schema

router = APIRouter()

@router.get("/", response_model=List[user_schema.User])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

@router.post("/", response_model=user_schema.User)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: user_schema.UserCreate,
) -> Any:
    """
    Create new user.
    """
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    user_obj = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=user_in.is_active,
    )
    db.add(user_obj)
    await db.commit()
    await db.refresh(user_obj)
    return user_obj


@router.get("/class-groups", response_model=List[user_schema.ClassGroup])
async def read_class_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
) -> Any:
    """
    Teacher view: list class groups with student count.
    """
    count_result = await db.execute(
        select(User.class_name, func.count(User.id))
        .where(User.role == "student", User.class_name.is_not(None))
        .group_by(User.class_name)
    )
    count_map = {row[0]: int(row[1]) for row in count_result.all()}

    groups_result = await db.execute(select(ClassGroup).order_by(ClassGroup.name.asc()))
    groups = groups_result.scalars().all()
    known_names = {g.name for g in groups}

    # Backward compatibility: auto-sync existing student class names into class_groups.
    missing_names = [name for name in count_map.keys() if name not in known_names]
    if missing_names:
        for name in missing_names:
            db.add(ClassGroup(name=name))
        await db.commit()
        groups_result = await db.execute(select(ClassGroup).order_by(ClassGroup.name.asc()))
        groups = groups_result.scalars().all()

    rows = [
        {
            "id": g.id,
            "name": g.name,
            "student_count": count_map.get(g.name, 0),
        }
        for g in groups
    ]

    rows.sort(key=lambda x: x["name"])
    return rows


@router.post("/class-groups", response_model=user_schema.ClassGroup)
async def create_class_group(
    *,
    db: AsyncSession = Depends(get_db),
    payload: user_schema.ClassGroupCreate,
    current_user: User = Depends(deps.get_current_teacher),
) -> Any:
    """
    Teacher action: create a class group.
    """
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Class name cannot be empty")

    existing_result = await db.execute(select(ClassGroup).where(ClassGroup.name == name))
    existing = existing_result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Class already exists")

    group = ClassGroup(name=name)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return {"id": group.id, "name": group.name, "student_count": 0}


@router.patch("/class-groups/{group_id}", response_model=user_schema.ClassGroup)
async def update_class_group(
    *,
    db: AsyncSession = Depends(get_db),
    group_id: int,
    payload: user_schema.ClassGroupUpdate,
    current_user: User = Depends(deps.get_current_teacher),
) -> Any:
    """
    Teacher action: rename class group and sync assigned students.
    """
    result = await db.execute(select(ClassGroup).where(ClassGroup.id == group_id))
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="Class not found")

    new_name = (payload.name or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Class name cannot be empty")

    if new_name != group.name:
        conflict_result = await db.execute(select(ClassGroup).where(ClassGroup.name == new_name))
        if conflict_result.scalars().first():
            raise HTTPException(status_code=400, detail="Class already exists")

        old_name = group.name
        group.name = new_name

        students_result = await db.execute(
            select(User).where(User.role == "student", User.class_name == old_name)
        )
        students = students_result.scalars().all()
        for student in students:
            student.class_name = new_name

    await db.commit()
    await db.refresh(group)

    cnt_result = await db.execute(
        select(func.count(User.id)).where(User.role == "student", User.class_name == group.name)
    )
    cnt = int(cnt_result.scalar() or 0)
    return {"id": group.id, "name": group.name, "student_count": cnt}


@router.delete("/class-groups/{group_id}", response_model=user_schema.ClassGroupDeleteResponse)
async def delete_class_group(
    *,
    db: AsyncSession = Depends(get_db),
    group_id: int,
    current_user: User = Depends(deps.get_current_teacher),
) -> Any:
    """
    Teacher action: delete class group and clear class assignment for its students.
    """
    result = await db.execute(select(ClassGroup).where(ClassGroup.id == group_id))
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="Class not found")

    students_result = await db.execute(
        select(User).where(User.role == "student", User.class_name == group.name)
    )
    students = students_result.scalars().all()
    for student in students:
        student.class_name = None

    await db.execute(delete(ClassGroup).where(ClassGroup.id == group_id))
    await db.commit()
    return {"deleted_count": 1, "cleared_students": len(students)}


@router.post("/register-student", response_model=user_schema.User)
async def register_student(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: user_schema.UserCreate,
) -> Any:
    """
    Public student registration endpoint.
    Role is always forced to student.
    """
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    user_obj = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role="student",
        is_active=True,
    )
    db.add(user_obj)
    await db.commit()
    await db.refresh(user_obj)
    return user_obj


@router.get("/students", response_model=List[user_schema.User])
async def read_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_teacher),
) -> Any:
    """
    Teacher view: list all student accounts.
    """
    result = await db.execute(
        select(User).where(User.role == "student").order_by(User.id.asc())
    )
    return result.scalars().all()


@router.patch("/students/{student_id}/class", response_model=user_schema.User)
async def update_student_class(
    *,
    db: AsyncSession = Depends(get_db),
    student_id: int,
    payload: user_schema.StudentClassUpdate,
    current_user: User = Depends(deps.get_current_teacher),
) -> Any:
    """
    Teacher action: assign/update student's class group.
    """
    result = await db.execute(
        select(User).where(User.id == student_id, User.role == "student")
    )
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    class_name = (payload.class_name or "").strip()
    student.class_name = class_name or None

    if class_name:
        existing_group_result = await db.execute(select(ClassGroup).where(ClassGroup.name == class_name))
        if not existing_group_result.scalars().first():
            db.add(ClassGroup(name=class_name))

    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/students/{student_id}", response_model=user_schema.StudentDeleteResponse)
async def delete_student_account(
    *,
    db: AsyncSession = Depends(get_db),
    student_id: int,
    current_user: User = Depends(deps.get_current_teacher),
) -> Any:
    """
    Teacher action: permanently delete a student account and related submissions.
    """
    result = await db.execute(
        select(User).where(User.id == student_id, User.role == "student")
    )
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    sub_result = await db.execute(select(Submission.id).where(Submission.student_id == student_id))
    submission_ids = [row[0] for row in sub_result.all()]

    if submission_ids:
        await db.execute(delete(Feedback).where(Feedback.submission_id.in_(submission_ids)))
        await db.execute(delete(StaticAnalysisResult).where(StaticAnalysisResult.submission_id.in_(submission_ids)))
        await db.execute(delete(ExecutionResult).where(ExecutionResult.submission_id.in_(submission_ids)))
        await db.execute(delete(Submission).where(Submission.id.in_(submission_ids)))

    await db.execute(delete(Enrollment).where(Enrollment.student_id == student_id))
    await db.execute(delete(User).where(User.id == student_id))
    await db.commit()
    return {"deleted_count": 1}

@router.get("/me", response_model=user_schema.User)
async def read_user_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.patch("/me", response_model=user_schema.User)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    payload: user_schema.UserSelfUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update current user profile (student/teacher self-service).
    """
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip() or None

    await db.commit()
    await db.refresh(current_user)
    return current_user

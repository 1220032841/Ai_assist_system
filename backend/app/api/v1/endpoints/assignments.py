from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.models import Assignment, User
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

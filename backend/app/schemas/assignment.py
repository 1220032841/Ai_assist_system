from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    course_id: Optional[int] = None


class Assignment(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True

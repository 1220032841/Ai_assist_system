from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    language: str = "cpp"
    starter_code: Optional[str] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    due_date: Optional[datetime] = None
    course_id: Optional[int] = None


class Assignment(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    language: str = "cpp"
    starter_code: Optional[str] = None
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssignmentDeleteResponse(BaseModel):
    deleted_id: int

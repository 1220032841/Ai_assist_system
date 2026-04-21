from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel

class SubmissionBase(BaseModel):
    assignment_id: int
    language: str = "python"
    code_content: str

class SubmissionCreate(SubmissionBase):
    pass

class Submission(SubmissionBase):
    id: int
    student_id: int
    version: int
    created_at: datetime
    status: Optional[str] = None
    
    class Config:
        from_attributes = True


class ExecutionResult(BaseModel):
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None

    class Config:
        from_attributes = True


class StaticAnalysisResult(BaseModel):
    issues: Optional[dict] = None
    score: Optional[float] = None

    class Config:
        from_attributes = True


class Feedback(BaseModel):
    content: str
    citations: Optional[Any] = None
    grade_breakdown: Optional[dict] = None
    final_score: Optional[float] = None

    class Config:
        from_attributes = True


class SubmissionDetail(Submission):
    execution_result: Optional[ExecutionResult] = None
    static_analysis: Optional[StaticAnalysisResult] = None
    feedback: Optional[Feedback] = None


class SubmissionBulkDeleteRequest(BaseModel):
    submission_ids: list[int]


class SubmissionDeleteResponse(BaseModel):
    deleted_count: int

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON, Text, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base import Base
import enum

class UserRole(str, enum.Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    class_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.STUDENT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    submissions: Mapped[List["Submission"]] = relationship(back_populates="student")
    courses_enrolled: Mapped[List["Enrollment"]] = relationship(back_populates="student")
    courses_teaching: Mapped[List["Course"]] = relationship(back_populates="instructor")


class ClassGroup(Base):
    __tablename__ = "class_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    term: Mapped[str] = mapped_column(String, nullable=True)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    instructor: Mapped["User"] = relationship(back_populates="courses_teaching")
    assignments: Mapped[List["Assignment"]] = relationship(back_populates="course")
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), primary_key=True)
    
    student: Mapped["User"] = relationship(back_populates="courses_enrolled")
    course: Mapped["Course"] = relationship(back_populates="enrollments")

class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String, nullable=False, default="cpp")
    starter_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example_input: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    allowed_concepts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # List of concepts
    rubric_id: Mapped[Optional[int]] = mapped_column(ForeignKey("rubrics.id"), nullable=True)

    course: Mapped["Course"] = relationship(back_populates="assignments")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="assignment")
    rubric: Mapped["Rubric"] = relationship(back_populates="assignments")

class Rubric(Base):
    __tablename__ = "rubrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    criteria: Mapped[dict] = mapped_column(JSON, nullable=False) # Structured rubric criteria
    
    assignments: Mapped[List["Assignment"]] = relationship(back_populates="rubric")

class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    code_content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String, default="python")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    assignment: Mapped["Assignment"] = relationship(back_populates="submissions")
    student: Mapped["User"] = relationship(back_populates="submissions")
    execution_result: Mapped["ExecutionResult"] = relationship(back_populates="submission", uselist=False)
    static_analysis: Mapped["StaticAnalysisResult"] = relationship(back_populates="submission", uselist=False)
    feedback: Mapped["Feedback"] = relationship(back_populates="submission", uselist=False)

    @property
    def status(self) -> str:
        if self.execution_result is None:
            return "pending"
        return "completed" if self.execution_result.exit_code == 0 else "failed"

class ExecutionResult(Base):
    __tablename__ = "execution_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), unique=True)
    stdout: Mapped[str] = mapped_column(Text, nullable=True)
    stderr: Mapped[str] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    memory_usage_mb: Mapped[float] = mapped_column(Integer, nullable=True) 
    
    submission: Mapped["Submission"] = relationship(back_populates="execution_result")

class StaticAnalysisResult(Base):
    __tablename__ = "static_analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), unique=True)
    issues: Mapped[dict] = mapped_column(JSON, nullable=True) # List of issues
    score: Mapped[float] = mapped_column(Integer, nullable=True) # Pylint score or similar
    
    submission: Mapped["Submission"] = relationship(back_populates="static_analysis")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False) # Markdown feedback
    citations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # List of citations
    grade_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # Score per criterion
    final_score: Mapped[Optional[float]] = mapped_column(Integer, nullable=True) 
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    submission: Mapped["Submission"] = relationship(back_populates="feedback")

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True) 
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536)) 

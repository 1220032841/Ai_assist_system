from typing import Optional
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    is_active: Optional[bool] = True
    full_name: Optional[str] = None
    class_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: str = "student"

class UserUpdate(UserBase):
    password: Optional[str] = None


class UserSelfUpdate(BaseModel):
    full_name: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str


class StudentClassUpdate(BaseModel):
    class_name: Optional[str] = None


class StudentDeleteResponse(BaseModel):
    deleted_count: int


class ClassGroupCreate(BaseModel):
    name: str


class ClassGroupUpdate(BaseModel):
    name: str


class ClassGroup(BaseModel):
    id: int
    name: str
    student_count: int = 0

    class Config:
        from_attributes = True


class ClassGroupDeleteResponse(BaseModel):
    deleted_count: int
    cleared_students: int

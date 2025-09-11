from pydantic import BaseModel, EmailStr
from typing import List, Optional
from .models import TaskStatus

class TaskOut(BaseModel):
    id: int
    title: str
    order: int
    status: TaskStatus
    class Config:
        from_attributes = True

class ProjectOut(BaseModel):
    id: int
    title: str
    description: str
    tasks: List[TaskOut]
    class Config:
        from_attributes = True

class UserRegisterIn(BaseModel):
    tg_id: str
    name: str
    email: EmailStr

class IdeaIn(BaseModel):
    tg_id: str
    idea: str

class UpdateTaskIn(BaseModel):
    task_id: int
    status: TaskStatus

class AdminLoginIn(BaseModel):
    email: EmailStr
    password: str

class AdminTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ReportOut(BaseModel):
    percent: float
    comment: str
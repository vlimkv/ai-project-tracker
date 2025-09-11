from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Task, TaskStatus, Project
from ..schemas import AdminLoginIn, AdminTokenOut
from ..auth import create_admin_token, require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

from os import getenv
ADMIN_EMAIL = getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = getenv("ADMIN_PASSWORD")

@router.post("/login", response_model=AdminTokenOut)
def login(payload: AdminLoginIn):
    if payload.email == ADMIN_EMAIL and payload.password == ADMIN_PASSWORD:
        return {"access_token": create_admin_token(payload.email)}
    raise HTTPException(401, "Invalid credentials")

@router.get("/users")
def users(db: Session = Depends(get_db), _=Depends(require_admin)):
    data = []
    for u in db.query(User).all():
        projects = []
        for p in u.projects:
            projects.append({
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "tasks": [{"id": t.id, "title": t.title, "order": t.order, "status": t.status} for t in p.tasks]
            })
        data.append({"id": u.id, "tg_id": u.tg_id, "name": u.name, "email": u.email, "projects": projects})
    return {"users": data}

@router.patch("/tasks/{task_id}")
def admin_update_task(task_id: int, status: TaskStatus, db: Session = Depends(get_db), _=Depends(require_admin)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = status
    db.commit()
    return {"ok": True}
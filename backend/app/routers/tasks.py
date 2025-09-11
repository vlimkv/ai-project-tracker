from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Task, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.patch("/{task_id}")
def update_task(task_id: int, status: TaskStatus, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = status
    db.commit()
    return {"ok": True}
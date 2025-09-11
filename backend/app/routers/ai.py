from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Project, Task, TaskStatus
from ..ai_service import review_progress

router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/report/{tg_id}")
def report(tg_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(tg_id=tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    tasks = [t for p in user.projects for t in p.tasks]
    total = len(tasks)
    done = len([t for t in tasks if t.status == TaskStatus.done])
    percent = round((done / total) * 100, 2) if total else 0.0
    comment = review_progress(percent)
    return {"percent": percent, "comment": comment}

@router.post("/review/{project_id}")
def review(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    total = len(project.tasks)
    done = len([t for t in project.tasks if t.status == TaskStatus.done])
    percent = round((done / total) * 100, 2) if total else 0.0
    comment = review_progress(percent)
    return {"percent": percent, "comment": comment}
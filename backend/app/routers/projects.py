from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Project, Task, TaskStatus
from ..schemas import IdeaIn
from ..ai_service import generate_description_and_tasks

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/idea")
def create_from_idea(payload: IdeaIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(tg_id=payload.tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    desc, tasks = generate_description_and_tasks(payload.idea)
    project = Project(user_id=user.id, title=payload.idea[:120], description=desc)
    db.add(project)
    db.flush()
    for i, t in enumerate(tasks):
        db.add(Task(project_id=project.id, title=t, order=i))
    db.commit()
    return {"project_id": project.id, "description": desc, "tasks": tasks}
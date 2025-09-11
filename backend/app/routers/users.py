from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..schemas import UserRegisterIn

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register")
def register(payload: UserRegisterIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(tg_id=payload.tg_id).first()
    if user:
        user.name = payload.name
        user.email = payload.email
    else:
        user = User(tg_id=payload.tg_id, name=payload.name, email=payload.email)
        db.add(user)
    db.commit()
    return {"ok": True}

@router.get("/{tg_id}/projects")
def list_projects(tg_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(tg_id=tg_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    data = []
    for p in user.projects:
        data.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "tasks": [{"id": t.id, "title": t.title, "order": t.order, "status": t.status} for t in p.tasks]
        })
    return {"projects": data}
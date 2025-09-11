from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import Base, engine
from .routers import users, projects, tasks, ai, admin
from .scheduler import start_scheduler
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Project Tracker API")

origins = [os.getenv("CORS_ORIGINS", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(ai.router)
app.include_router(admin.router)

@app.get("/health")
async def health():
    return {"ok": True}

start_scheduler()
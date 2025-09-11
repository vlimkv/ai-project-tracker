import os
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
import httpx
from .db import SessionLocal
from .models import User, TaskStatus

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_API = os.getenv("TELEGRAM_API_BASE", "https://api.telegram.org")

scheduler = BackgroundScheduler()

async def send_daily_reports():
    if not BOT_TOKEN:
        return
    db: Session = SessionLocal()
    try:
        users = db.query(User).all()
        for u in users:
            tasks = [t for p in u.projects for t in p.tasks]
            total = len(tasks)
            done = len([t for t in tasks if t.status == TaskStatus.done])
            percent = round((done / total) * 100, 2) if total else 0.0
            text = f"Ваш ежедневный прогресс: {percent}% выполнено. Продолжайте!"
            async with httpx.AsyncClient() as client:
                await client.post(f"{TG_API}/bot{BOT_TOKEN}/sendMessage", json={"chat_id": u.tg_id, "text": text})
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(lambda: __import__("asyncio").run(send_daily_reports()), "interval", hours=24, id="daily_reports", replace_existing=True)
    scheduler.start()
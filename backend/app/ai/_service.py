import os, hashlib, json
from typing import List, Tuple
import redis

REDIS_URL = os.getenv("REDIS_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

r = redis.from_url(REDIS_URL) if REDIS_URL else None

STUB_TASKS = [
    "Сформулировать value‑prop и целевую аудиторию",
    "Спроектировать схему БД (пользователи/проекты/задачи)",
    "Собрать FastAPI backend и миграции",
    "Написать Telegram‑бот (/start, /idea, /projects, /update, /report)",
    "Собрать веб‑панель (login, таблица, AI Review)",
    "Настроить Docker/CI и деплой",
]


def _cache_get(key: str):
    if not r: return None
    val = r.get(key)
    return json.loads(val) if val else None

def _cache_set(key: str, value, ttl=3600):
    if not r: return
    r.setex(key, ttl, json.dumps(value, ensure_ascii=False))


def generate_description_and_tasks(idea: str) -> Tuple[str, List[str]]:
    key = f"ai:roadmap:{hashlib.sha256(idea.encode()).hexdigest()}"
    cached = _cache_get(key)
    if cached:
        return cached["description"], cached["tasks"]

    description = f"Идея: {idea}. Цель — собрать работающий MVP с измеримым прогрессом."
    tasks = STUB_TASKS[:]

    result = {"description": description, "tasks": tasks}
    _cache_set(key, result)
    return description, tasks


def review_progress(percent: float) -> str:
    if percent >= 80:
        return "Прогресс отличный. Зафиксируйте результаты и запланируйте релиз/обратную связь от пользователей."
    if percent >= 50:
        return "Движение хорошее. Сфокусируйтесь на задачах с наибольшей ценностью (бот команды, отчёты)."
    return "Начните с базовых вещей: регистрация, хранение идей, одна сквозная AI‑операция. Уберите лишнее."
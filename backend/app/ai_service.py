import os, json, hashlib, re
from typing import List, Tuple

# ---- Redis ----
try:
    import redis
except Exception:
    redis = None

REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL) if (redis and REDIS_URL) else None

PROVIDER = os.getenv("AI_PROVIDER", "stub")
OSS_BASE_URL = os.getenv("OSS_BASE_URL", "http://llm:8080/v1")
OSS_MODEL = os.getenv("OSS_MODEL", "gpt-oss-20b")
OSS_API_KEY = os.getenv("OSS_API_KEY", "local")

def _cache_get(k: str):
    if not r: return None
    v = r.get(k)
    return json.loads(v) if v else None

def _cache_set(k: str, val, ttl=3600):
    if r: r.setex(k, ttl, json.dumps(val, ensure_ascii=False))

def _extract_json(text: str):
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    raise ValueError("LLM: не удалось распарсить JSON")

def _oss_generate(idea: str):
    from openai import OpenAI
    client = OpenAI(base_url=OSS_BASE_URL, api_key=OSS_API_KEY)

    sys = (
        "Ты продакт-менеджер. Коротко опиши идею (1–2 предложения) и дай РОВНО 6 "
        "конкретных задач MVP. Ответ строго в JSON:\n"
        '{ "description": "…", "tasks": ["…","…","…","…","…","…"] }\n'
        "Никакого текста вне JSON."
    )
    user = f"Идея: {idea}"

    resp = client.chat.completions.create(
        model=OSS_MODEL,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    content = resp.choices[0].message.content or ""
    data = _extract_json(content)

    desc = str(data.get("description", "")).strip()
    tasks = [str(t).strip() for t in (data.get("tasks") or []) if str(t).strip()]
    if not desc or not tasks:
        raise ValueError("LLM: пустой ответ")
    return desc, tasks[:7]

STUB = [
    "Сформулировать value-prop и ЦА",
    "Спроектировать БД: users/projects/tasks",
    "Поднять FastAPI + миграции",
    "Собрать Telegram-бот: /start /idea /projects /update /report",
    "Сделать веб-панель (login, список, AI Review)",
    "Docker-compose, README, деплой",
]

def generate_description_and_tasks(idea: str) -> Tuple[str, List[str]]:
    key = "ai:roadmap:" + hashlib.sha256(idea.encode()).hexdigest()
    if (cached := _cache_get(key)):
        return cached["description"], cached["tasks"]

    try:
        if PROVIDER == "oss":
            desc, tasks = _oss_generate(idea)
        else:
            raise RuntimeError("stub")
    except Exception:
        desc = f"Идея: {idea}. Цель — быстро собрать MVP и проверить гипотезы."
        tasks = STUB

    _cache_set(key, {"description": desc, "tasks": tasks})
    return desc, tasks

def review_progress(percent: float) -> str:
    if percent >= 80:
        return "Прогресс отличный — готовьте релиз, проведите ретро и стабилизацию."
    if percent >= 50:
        return "Движение хорошее. Сфокусируйтесь на задачах с наибольшей ценностью."
    return "Соберите сквозной MVP и уберите ключевые блокеры."
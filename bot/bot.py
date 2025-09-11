# bot/bot.py
import os, re, html, logging, contextlib, math, asyncio, random
from typing import Optional, List, Dict

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, StateFilter
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ChatAction

import httpx

logging.basicConfig(level=logging.INFO)

# ---------- ENV ----------
API_BASE = os.getenv("API_BASE") or os.getenv("NEXT_PUBLIC_API_BASE_URL", "http://backend:8000")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

# ---------- BOT / DP ----------
bot = Bot(
    token=TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML"),
)
storage = RedisStorage.from_url(REDIS_URL) if REDIS_URL else MemoryStorage()
dp = Dispatcher(storage=storage)

# ---------- HTTP ----------
def client() -> httpx.AsyncClient:
    # читаем до 60с — локальная модель может думать подольше
    return httpx.AsyncClient(base_url=API_BASE, timeout=httpx.Timeout(60.0, connect=5.0))

# ---------- Helpers ----------
E = html.escape
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_email(s: str) -> bool: return bool(EMAIL_RE.match((s or "").strip()))
def norm(s: Optional[str]) -> str: return (s or "").strip()

def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆕 Идея"), KeyboardButton(text="📋 Проекты")],
            [KeyboardButton(text="✏️ Обновить"), KeyboardButton(text="📊 Отчёт")],
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="⛔ Отмена")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие или напиши идею…",
        selective=True,
    )

def progress_bar(percent: int, width: int = 12) -> str:
    percent = max(0, min(100, percent))
    filled = int(round(percent / 100 * width))
    return f"[{'█'*filled}{'░'*(width-filled)}] {percent}%"

async def run_progress(chat_id: int, msg: Message) -> None:
    """
    Мягкая анимация прогресса, до 95% (чтобы был зазор на финиш).
    Останавливается через cancel() из вызывающего кода.
    """
    p = 0
    try:
        while True:
            p = min(95, p + random.randint(1, 3))
            await bot.send_chat_action(chat_id, ChatAction.TYPING)
            await msg.edit_text(f"⚙️ Генерирую план…\n<code>{progress_bar(p)}</code>")
            await asyncio.sleep(0.4)
    except asyncio.CancelledError:
        # тихо выходим
        raise

# ---------- FSM ----------
class Reg(StatesGroup):
    name = State()
    email = State()

class Idea(StatesGroup):
    waiting = State()

# ---------- /start /help /cancel ----------
@dp.message(Command("start"))
async def start_cmd(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(
        "Привет! Давай зарегистрируемся.\n\n"
        "<b>Как тебя зовут?</b>\n"
        "Можно сразу прислать e-mail — я пойму.",
        reply_markup=main_kb()
    )
    await state.set_state(Reg.name)

@dp.message(Command("help"))
@dp.message(F.text == "❓ Помощь")
async def help_cmd(m: Message):
    await m.answer(
        "Что умею:\n"
        "• <b>🆕 Идея</b> — пришлёшь описание, соберу краткое описание и 6 задач MVP\n"
        "• <b>📋 Проекты</b> — покажу все твои проекты и задачи\n"
        "• <b>✏️ Обновить</b> — кнопками: проект → задача → статус\n"
        "• <b>📊 Отчёт</b> — короткий комментарий по прогрессу\n"
        "• <b>⛔ Отмена</b> — сбросить текущий шаг",
        reply_markup=main_kb()
    )

@dp.message(Command("cancel"))
@dp.message(F.text == "⛔ Отмена")
async def cancel_cmd(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Окей, отменил. Что дальше?", reply_markup=main_kb())

# ---------- Регистрация ----------
@dp.message(Reg.name, F.text)
async def reg_name(m: Message, state: FSMContext):
    text = norm(m.text)
    if not text:
        return await m.answer("Введи имя, пожалуйста 🙂")

    if is_email(text):
        await state.update_data(email=text)
        return await m.answer("Окей, e-mail записал. <b>А как тебя зовут?</b>")

    await state.update_data(name=text)
    data = await state.get_data()

    if is_email(data.get("email", "")):
        async with client() as cl:
            await cl.post("/users/register", json={
                "tg_id": str(m.chat.id),
                "name": data["name"],
                "email": data["email"],
            })
        await state.clear()
        return await m.answer("Готово! Ты в системе. Жми «🆕 Идея» и опиши свою идею.", reply_markup=main_kb())

    await state.set_state(Reg.email)
    await m.answer("Отлично. Теперь введи <b>e-mail</b>:")

@dp.message(Reg.email, F.text)
async def reg_email(m: Message, state: FSMContext):
    email = norm(m.text)
    if not is_email(email):
        return await m.answer("Похоже на неверный e-mail. Пример: <code>you@example.com</code>")

    data = await state.get_data()
    name = norm(data.get("name"))

    if not name:
        await state.update_data(email=email)
        await state.set_state(Reg.name)
        return await m.answer("E-mail записал. Теперь введи <b>имя</b>:")

    async with client() as cl:
        await cl.post("/users/register", json={
            "tg_id": str(m.chat.id),
            "name": name,
            "email": email,
        })

    await state.clear()
    await m.answer("Готово! Жми «🆕 Идея» и опиши свою идею.", reply_markup=main_kb())

# ---------- Идея (кнопка) ----------
@dp.message(Command("idea"))
@dp.message(F.text == "🆕 Идея")
async def idea_cmd(m: Message, state: FSMContext):
    await state.set_state(Idea.waiting)
    await m.answer("Пришли <b>текст идеи</b> одним сообщением — я сгенерирую описание и 6 задач MVP.")

@dp.message(Idea.waiting, F.text & ~F.text.startswith("/"))
async def idea_text(m: Message, state: FSMContext):
    text = norm(m.text)
    if len(text) < 8:
        return await m.answer("Идея слишком короткая. Добавь деталей и пришли снова.")

    # стартовое сообщение + анимация прогресса
    progress_msg = await m.answer(f"⚙️ Генерирую план…\n<code>{progress_bar(0)}</code>")
    progress_task = asyncio.create_task(run_progress(m.chat.id, progress_msg))

    try:
        async with client() as cl:
            r = await cl.post("/projects/idea", json={"tg_id": str(m.chat.id), "idea": text})
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        progress_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await progress_task
        await state.clear()
        return await progress_msg.edit_text(
            f"❌ Не вышло сгенерировать план:\n<code>{E(str(e))}</code>",
            reply_markup=None
        )

    # останавливаем анимацию, добиваем до 100%, показываем результат
    progress_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await progress_task
    await progress_msg.edit_text(f"✅ Готово!\n<code>{progress_bar(100)}</code>")

    desc = E(data.get("description", ""))
    tasks = data.get("tasks", []) or []
    tasks_text = "\n".join(f"{i+1}. {E(str(t))}" for i, t in enumerate(tasks))
    await state.clear()
    await m.answer(
        f"<b>Описание</b>:\n{desc}\n\n<b>Roadmap</b>:\n{tasks_text}",
        reply_markup=main_kb()
    )

# ---------- Проекты ----------
@dp.message(Command("projects"))
@dp.message(F.text == "📋 Проекты")
async def projects_cmd(m: Message):
    try:
        async with client() as cl:
            r = await cl.get(f"/users/{m.chat.id}/projects")
            r.raise_for_status()
            res = r.json()
    except Exception as e:
        return await m.answer(f"Не смог получить проекты: <code>{E(str(e))}</code>", reply_markup=main_kb())

    projects = res.get("projects") or []
    if not projects:
        return await m.answer("Пока нет проектов. Нажми «🆕 Идея».", reply_markup=main_kb())

    lines: List[str] = []
    for p in projects:
        title = E(p.get("title", ""))
        descr = E(p.get("description", ""))
        lines.append(f"\n— <b>{title}</b>\n<i>{descr}</i>")
        for t in sorted(p.get("tasks", []), key=lambda k: k["order"]):
            lines.append(f"  {t['order']+1}) {E(t.get('title',''))} — <code>{E(t.get('status',''))}</code>")

    await m.answer("\n".join(lines), reply_markup=main_kb())

# ---------- Обновление статусов: проекты → задачи → статус ----------
PAGE_SIZE = 8  # по 8 проектов на экран

def paginate(items: List[Dict], page: int, size: int) -> List[Dict]:
    start = page * size
    return items[start:start+size]

def build_projects_kb(projects: List[Dict], page: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    page = max(0, page)
    total_pages = max(1, math.ceil(len(projects) / PAGE_SIZE))

    for p in paginate(projects, page, PAGE_SIZE):
        title = (p.get("title") or "")[:40]
        kb.button(text=f"• {title}", callback_data=f"upd:p:{p['id']}")

    if total_pages > 1:
        if page > 0:
            kb.button(text="◀️ Назад", callback_data=f"upd:pg:{page-1}")
        kb.button(text=f"{page+1}/{total_pages}", callback_data="upd:noop:pp")
        if page < total_pages - 1:
            kb.button(text="Вперёд ▶️", callback_data=f"upd:pg:{page+1}")

    kb.adjust(1)
    if total_pages > 1:
        kb.adjust(1, 1, 1)

    return kb

def build_tasks_kb(project_id: int, tasks: List[Dict]) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for t in sorted(tasks, key=lambda k: k["order"]):
        label = f"{t['order']+1}. {t['title'][:40]}"
        kb.button(text=label, callback_data=f"upd:t:{project_id}:{t['id']}")
    kb.button(text="« К проектам", callback_data="upd:back:projects")
    kb.adjust(1)
    return kb

def build_status_kb(task_id: int, project_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="⏳ pending",      callback_data=f"upd:s:pending:{task_id}:{project_id}")
    kb.button(text="🔧 in_progress",  callback_data=f"upd:s:in_progress:{task_id}:{project_id}")
    kb.button(text="✅ done",         callback_data=f"upd:s:done:{task_id}:{project_id}")
    kb.button(text="« К задачам",     callback_data=f"upd:back:tasks:{project_id}")
    kb.adjust(1)
    return kb

@dp.message(Command("update"))
@dp.message(F.text == "✏️ Обновить")
async def update_entry(m: Message):
    try:
        async with client() as cl:
            r = await cl.get(f"/users/{m.chat.id}/projects")
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return await m.answer(f"Не удалось получить проекты: <code>{E(str(e))}</code>", reply_markup=main_kb())

    projects = data.get("projects") or []
    if not projects:
        return await m.answer("Нет проектов. Нажми «🆕 Идея».", reply_markup=main_kb())

    kb = build_projects_kb(projects, page=0)
    await m.answer("Выбери проект:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("upd:pg:"))
async def upd_projects_page(cb: CallbackQuery):
    try:
        page = int(cb.data.split(":")[2])
    except Exception:
        return await cb.answer("Ошибка пагинации", show_alert=True)

    async with client() as cl:
        r = await cl.get(f"/users/{cb.from_user.id}/projects")
        r.raise_for_status()
        data = r.json()

    projects = data.get("projects") or []
    if not projects:
        await cb.message.edit_text("Нет проектов. Нажми «🆕 Идея».", reply_markup=None)
        return await cb.answer()

    kb = build_projects_kb(projects, page=page)
    await cb.message.edit_text("Выбери проект:", reply_markup=kb.as_markup())
    await cb.answer()

@dp.callback_query(F.data == "upd:back:projects")
async def upd_back_projects(cb: CallbackQuery):
    return await upd_projects_page(
        CallbackQuery.model_construct(**{**cb.model_dump(), "data": "upd:pg:0"})
    )

@dp.callback_query(F.data.startswith("upd:p:"))
async def upd_choose_project(cb: CallbackQuery):
    try:
        project_id = int(cb.data.split(":")[2])
    except Exception:
        return await cb.answer("Ошибка выбора проекта", show_alert=True)

    try:
        async with client() as cl:
            r = await cl.get(f"/users/{cb.from_user.id}/projects")
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return await cb.answer(f"Ошибка API: {E(str(e))}", show_alert=True)

    projects = data.get("projects") or []
    project = next((p for p in projects if p["id"] == project_id), None)
    if not project:
        return await cb.answer("Проект не найден", show_alert=True)

    tasks = project.get("tasks") or []
    if not tasks:
        return await cb.answer("В проекте нет задач", show_alert=True)

    kb = build_tasks_kb(project_id, tasks)
    await cb.message.edit_text(f"<b>{E(project.get('title','Проект'))}</b>\nВыбери задачу:", reply_markup=kb.as_markup())
    await cb.answer()

@dp.callback_query(F.data.startswith("upd:back:tasks:"))
async def upd_back_tasks(cb: CallbackQuery):
    try:
        project_id = int(cb.data.split(":")[3])
    except Exception:
        return await cb.answer("Ошибка возврата", show_alert=True)

    cb.data = f"upd:p:{project_id}"
    return await upd_choose_project(cb)

@dp.callback_query(F.data.startswith("upd:t:"))
async def upd_choose_task(cb: CallbackQuery):
    try:
        _, _, project_id_str, task_id_str = cb.data.split(":")
        task_id = int(task_id_str)
        project_id = int(project_id_str)
    except Exception:
        return await cb.answer("Ошибка выбора задачи", show_alert=True)

    kb = build_status_kb(task_id, project_id)
    await cb.message.edit_text("Выбери новый статус:", reply_markup=kb.as_markup())
    await cb.answer()

@dp.callback_query(F.data.startswith("upd:s:"))
async def upd_set_status(cb: CallbackQuery):
    try:
        _, _, status, task_id_str, project_id_str = cb.data.split(":")
        task_id = int(task_id_str)
        project_id = int(project_id_str)
        assert status in {"pending", "in_progress", "done"}
    except Exception:
        return await cb.answer("Неверные данные", show_alert=True)

    try:
        async with client() as cl:
            await cl.patch(f"/tasks/{task_id}", params={"status": status})
    except Exception as e:
        return await cb.answer(f"Ошибка API: {E(str(e))}", show_alert=True)

    await cb.message.edit_text(f"Статус обновлён: <b>{E(status)}</b> ✅", reply_markup=None)
    await cb.answer("Обновлено")

# ---------- Отчёт ----------
@dp.message(Command("report"))
@dp.message(F.text == "📊 Отчёт")
async def report_cmd(m: Message):
    try:
        async with client() as cl:
            r = await cl.get(f"/ai/report/{m.chat.id}")
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return await m.answer(f"Не удалось получить отчёт: <code>{E(str(e))}</code>", reply_markup=main_kb())

    percent = data.get("percent", 0)
    comment = E(data.get("comment", "—"))
    await m.answer(f"Готово! Выполнено: <b>{percent}%</b>.\nКомментарий: {comment}", reply_markup=main_kb())

# ---------- Fallback ----------
@dp.message()
async def fallback(m: Message):
    await m.answer("Не понял. Выбери кнопку ниже или напиши «🆕 Идея».", reply_markup=main_kb())

# ---------- ENTRY ----------
if __name__ == "__main__":
    async def main():
        me = await bot.get_me()
        logging.info("Polling started as @%s", me.username)
        await dp.start_polling(bot)
    asyncio.run(main())
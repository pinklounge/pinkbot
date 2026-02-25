import os
import re
import time
import sqlite3
import traceback
from datetime import datetime, timedelta, timezone

import telebot
from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

# ================== CONFIG ==================
# Railway Variables (recommended):
# BOT_TOKEN, ADMIN_ID, BOOK_URL, DB_FILE

TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
if not TOKEN or ":" not in TOKEN:
    raise RuntimeError("❌ BOT_TOKEN is missing/invalid. Set Railway Variable BOT_TOKEN.")

ADMIN_ID = int((os.getenv("ADMIN_ID") or "0").strip() or "0")  # can be 0 if not set (no admin)
BOOK_URL = (os.getenv("BOOK_URL") or "https://www.instagram.com/rozhevyi.sushi.lounge/").strip()
DB_FILE = (os.getenv("DB_FILE") or "pink_lounge.db").strip()

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

apihelper.CONNECT_TIMEOUT = 10
apihelper.READ_TIMEOUT = 30

# ================== TIME ==================
def utcnow() -> datetime:
    return datetime.now(timezone.utc)

ANIM_DELAY = 0.18
COMMENT_MAX = 100
VISIT_COOLDOWN_HOURS = 24

# ================== MENU ==================
MENU = {
    "Авторські Кальяни": {
        "SIGNATURE_TROPICAL": {
            "title": "Тропічний Signature 🍍🥭",
            "price": 550,
            "desc": (
                "✧ *Авторський кальян* ✧\n"
                "Соковита тропічна база з мʼякою текстурою та насиченим ароматом.\n"
                "Теплий, солодкий і збалансований профіль.\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🌴 *Recommended*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🌴 *Golden Safari* ✧\n"
                "│ Манго · Груша · Ківі\n\n"
                "🏝️ *Peach Island* ✧\n"
                "│ Персик · Ананас · Яблуко\n\n"
                "🥥 *Coconut Mirage* ✧\n"
                "│ Банан · Кокос · Апельсин\n"
            ),
            "photo_file_id": None,
            "video_file_id": None,
        },
        "SIGNATURE_CITRUS": {
            "title": "Цитрусовий Signature 🍊🍋",
            "price": 550,
            "desc": (
                "✧ *Авторський кальян* ✧\n"
                "Яскравий цитрусовий характер з освіжаючою кислинкою.\n"
                "Чисте та драйвове розкриття смаку.\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🍋 *Recommended*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🍋 *Italian Spark* ✧\n"
                "│ Лімончело\n\n"
                "🍑 *Amber Citrus* ✧\n"
                "│ Лимон · Персик · Апельсин\n\n"
                "🥧 *Citrus Crème* ✧\n"
                "│ Лимонний пиріг\n"
            ),
            "photo_file_id": None,
            "video_file_id": None,
        },
        "SIGNATURE_BERRY": {
            "title": "Ягідний Signature 🍓🫐",
            "price": 550,
            "desc": (
                "✧ *Авторський кальян* ✧\n"
                "Глибокий ягідний букет з насиченим ароматом.\n"
                "Соковитий, яскравий та димний профіль.\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🍓 *Recommended*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🍬 *Berry Candy* ✧\n"
                "│ Кисла малина · Вишня\n\n"
                "🌹 *Ruby Garden* ✧\n"
                "│ Полуничний крем · Гранат · Мʼята\n\n"
                "🍸 *Clover Club* ✧\n"
                "│ Малина · Персик · Джин\n"
            ),
            "photo_file_id": None,
            "video_file_id": None,
        },
        "SIGNATURE_ANCHAN": {
            "title": "Anchan Signature 🔵🍵",
            "price": 550,
            "desc": (
                "✧ *Авторський кальян на чаї анчан* ✧\n"
                "Глибокий сапфіровий відтінок та делікатна чайна основа.\n"
                "Естетика, смак і ритуал в одному форматі.\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🔵 *Recommended*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🔵 *Blue Ceremony* ✧\n"
                "│ Чай · Манго · Ананас\n\n"
                "🌲 *Forest Eclipse* ✧\n"
                "│ Диня · Смородина · Хвоя\n\n"
                "🌙 *Midnight Bloom* ✧\n"
                "│ Чорниця · Вишня · Чай\n"
            ),
            "photo_file_id": None,
            "video_file_id": None,
        },
        "SIGNATURE_PINK": {
            "title": "Pink Signature 🌸",
            "price": 550,
            "desc": (
                "✧ *Авторський кальян* ✧\n"
                "Натхненний атмосферою Рожевого.\n"
                "Мʼякий, ароматний і стильний формат.\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "🌸 *Recommended*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "💘 *Cupidon* ✧\n"
                "│ Ягідний коктейль з легким відтінком кокосу\n\n"
                "🥛 *Pink Milk* ✧\n"
                "│ Мілкшейк Банан · Виноград\n\n"
                "🍒 *Drunk Cherry* ✧\n"
                "│ Десерт «пʼяна вишня»\n"
            ),
            "photo_file_id": None,
            "video_file_id": None,
        },
    },
    "Фруктові Чаші": {
        "BOWL_GRAPEFRUIT": {
            "title": "Чаша Грейпфрут 🍊",
            "price": 680,
            "desc": (
                "✧ *Фруктова чаша* ✧\n"
                "Натуральна основа з яскравим цитрусовим характером.\n"
                "Легка гірчинка додає глибини смаку.\n"
                "Ефектна подача та насичений аромат з першої затяжки."
            ),
            "photo_file_id": None,
            "video_file_id": None,
        },
        "BOWL_ORANGE": {
            "title": "Чаша Апельсин 🍊",
            "price": 630,
            "desc": (
                "✧ *Фруктова чаша* ✧\n"
                "Солодкий і мʼякий цитрусовий профіль.\n"
                "Надає кальяну соковитість і легкість.\n"
                "Ідеальний вибір для тропічних та цитрусових міксів."
            ),
            "photo_file_id": None,
            "video_file_id": None,
        },
    },
    "Формат": {
        "STANDARD_CLASSIC": {
            "title": "Класика ⚪️",
            "price": 480,
            "desc": (
                "✧ *Посадка: Класика* ✧\n"
                "Рівне прогрівання та стабільний смак.\n"
                "Універсальний формат для будь-яких тютюнів.\n"
                "Збалансований варіант без експериментів."
            ),
            "photo_file_id": None,
            "video_file_id": None,
        },
        "STANDARD_PILLOW": {
            "title": "Подушка 🧱",
            "price": 520,
            "desc": (
                "✧ *Посадка: Подушка* ✧\n"
                "Щільніший дим та більш насичене розкриття.\n"
                "Підходить для тих, хто любить міцніше.\n"
                "Довше тримає жар і інтенсивність."
            ),
            "photo_file_id": None,
            "video_file_id": None,
        },
        "STANDARD_OVERPACK": {
            "title": "Оверпак 🔥",
            "price": 520,
            "desc": (
                "✧ *Посадка: Оверпак* ✧\n"
                "Максимально яскраве розкриття смаку.\n"
                "Швидкий прогрів та густий дим.\n"
                "Рекомендовано для досвідчених гостей."
            ),
            "photo_file_id": None,
            "video_file_id": None,
        },
    },
}

CATEGORY_DESC = {
    "Авторські Кальяни": (
        "🌸 ✧ *SIGNATURE COLLECTION* ✧\n\n"
        "Авторські мікси з характером.\n"
        "Мʼяка подача · чистий профіль · рівний дим."
    ),
    "Фруктові Чаші": (
        "🍊 ✧ *FRUIT BOWLS* ✧\n\n"
        "Соковита подача та яскраве розкриття.\n"
        "Ефектно · ароматно · преміум."
    ),
    "Формат": (
        "⚙️ ✧ *FORMAT* ✧\n\n"
        "Посадка — це стиль смаку.\n"
        "Контроль · стабільність · інтенсивність."
    ),
}

# ================== DB ==================
def db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def _column_exists(cur, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            created_at TEXT,
            visits INTEGER DEFAULT 0,
            last_visit TEXT,
            status TEXT DEFAULT 'Guest',
            favorite_key TEXT,
            favorite_mix TEXT,
            last_table TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ui (
            chat_id INTEGER PRIMARY KEY,
            main_message_id INTEGER,
            aux_message_id INTEGER,
            admin_message_id INTEGER,
            main_kind TEXT DEFAULT 'text'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            created_at TEXT,
            kind TEXT,
            item_key TEXT,
            rating INTEGER,
            text TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS state (
            chat_id INTEGER PRIMARY KEY,
            awaiting_comment INTEGER DEFAULT 0,
            awaiting_fav_mix INTEGER DEFAULT 0,
            pending_kind TEXT,
            pending_item_key TEXT,
            pending_rating INTEGER,
            pending_fav_item_key TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_media (
            item_key TEXT PRIMARY KEY,
            photo_file_id TEXT,
            video_file_id TEXT,
            updated_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_overrides (
            item_key TEXT PRIMARY KEY,
            title TEXT,
            desc TEXT,
            price INTEGER,
            updated_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            chat_id INTEGER PRIMARY KEY,
            admin_mode INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_media_state (
            admin_id INTEGER PRIMARY KEY,
            mode TEXT,
            item_key TEXT,
            updated_at TEXT
        )
    """)

    conn.commit()
    conn.close()

def migrate_db():
    conn = db()
    cur = conn.cursor()

    for col in ("aux_message_id", "admin_message_id", "main_kind"):
        if not _column_exists(cur, "ui", col):
            if col == "main_kind":
                cur.execute("ALTER TABLE ui ADD COLUMN main_kind TEXT DEFAULT 'text'")
            else:
                cur.execute(f"ALTER TABLE ui ADD COLUMN {col} INTEGER")

    if not _column_exists(cur, "users", "favorite_mix"):
        cur.execute("ALTER TABLE users ADD COLUMN favorite_mix TEXT")

    if not _column_exists(cur, "state", "awaiting_fav_mix"):
        cur.execute("ALTER TABLE state ADD COLUMN awaiting_fav_mix INTEGER DEFAULT 0")
    if not _column_exists(cur, "state", "pending_fav_item_key"):
        cur.execute("ALTER TABLE state ADD COLUMN pending_fav_item_key TEXT")

    conn.commit()
    conn.close()

def ensure_user(chat_id: int):
    conn = db()
    cur = conn.cursor()

    cur.execute("INSERT OR IGNORE INTO users(chat_id, created_at) VALUES(?, ?)", (chat_id, utcnow().isoformat()))
    cur.execute("INSERT OR IGNORE INTO state(chat_id, awaiting_comment, awaiting_fav_mix) VALUES(?, 0, 0)", (chat_id,))
    cur.execute("INSERT OR IGNORE INTO settings(chat_id, admin_mode) VALUES(?, 0)", (chat_id,))
    cur.execute("""
        INSERT OR IGNORE INTO ui(chat_id, main_message_id, aux_message_id, admin_message_id, main_kind)
        VALUES(?, NULL, NULL, NULL, 'text')
    """, (chat_id,))

    conn.commit()
    conn.close()

def get_user(chat_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_state(chat_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM state WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    conn.close()
    return row

def set_state(chat_id: int, awaiting_comment: int, kind=None, item_key=None, rating=None):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE state
        SET awaiting_comment=?, pending_kind=?, pending_item_key=?, pending_rating=?
        WHERE chat_id=?
    """, (awaiting_comment, kind, item_key, rating, chat_id))
    conn.commit()
    conn.close()

def set_fav_mix_state(chat_id: int, awaiting: int, item_key: str | None):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE state
        SET awaiting_fav_mix=?, pending_fav_item_key=?
        WHERE chat_id=?
    """, (awaiting, item_key, chat_id))
    conn.commit()
    conn.close()

def is_admin_mode(chat_id: int) -> bool:
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT admin_mode FROM settings WHERE chat_id=?", (chat_id,))
    r = cur.fetchone()
    conn.close()
    return bool(r and int(r["admin_mode"] or 0) == 1)

def set_admin_mode(chat_id: int, val: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings(chat_id, admin_mode)
        VALUES(?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET admin_mode=excluded.admin_mode
    """, (chat_id, val))
    conn.commit()
    conn.close()

def get_ui(chat_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ui WHERE chat_id=?", (chat_id,))
    r = cur.fetchone()
    conn.close()
    return r

def set_ui_fields(chat_id: int, **kwargs):
    if not kwargs:
        return
    conn = db()
    cur = conn.cursor()
    keys = list(kwargs.keys())
    sets = ", ".join([f"{k}=?" for k in keys])
    vals = [kwargs[k] for k in keys]
    vals.append(chat_id)
    cur.execute(f"UPDATE ui SET {sets} WHERE chat_id=?", vals)
    conn.commit()
    conn.close()

def safe_delete(chat_id: int, mid: int | None):
    if not mid:
        return
    try:
        bot.delete_message(chat_id, mid)
    except Exception:
        pass

def typing(chat_id: int):
    try:
        bot.send_chat_action(chat_id, "typing")
    except Exception:
        pass
    time.sleep(ANIM_DELAY)

def header(title: str) -> str:
    return f"✧ *{title}* ✧\n━━━━━━━━━━━━━━━━━━\n"

def status_from_visits(v: int) -> str:
    if v >= 60: return "Black Edition"
    if v >= 30: return "Signature Member"
    if v >= 10: return "Pink Insider"
    return "Guest"

def parse_iso(dt_str: str) -> datetime | None:
    if not dt_str:
        return None
    try:
        d = datetime.fromisoformat(dt_str)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None

def extract_table_code(raw: str | None) -> str | None:
    if not raw:
        return None
    sp = raw.strip().lower()
    m = re.match(r"^(t\d+)$", sp)
    return m.group(1) if m else None

def try_checkin(chat_id: int, table_code: str | None):
    u = get_user(chat_id)
    now = utcnow()

    if u and u["last_visit"]:
        last = parse_iso(u["last_visit"])
        if last and (now - last) < timedelta(hours=VISIT_COOLDOWN_HOURS):
            return False

    visits = int((u["visits"] if u else 0) or 0) + 1
    st = status_from_visits(visits)

    conn = db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET visits=?, last_visit=?, status=?, last_table=?
        WHERE chat_id=?
    """, (visits, now.isoformat(), st, table_code, chat_id))
    conn.commit()
    conn.close()
    return True

def set_favorite_mix(chat_id: int, item_key: str, mix_text: str | None):
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET favorite_key=?, favorite_mix=? WHERE chat_id=?", (item_key, mix_text, chat_id))
    conn.commit()
    conn.close()

def clear_favorite(chat_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET favorite_key=NULL, favorite_mix=NULL WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()

def add_feedback(chat_id: int, kind: str, rating: int, item_key: str | None, text: str | None):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO feedback(chat_id, created_at, kind, item_key, rating, text)
        VALUES(?,?,?,?,?,?)
    """, (chat_id, utcnow().isoformat(), kind, item_key, rating, text))
    conn.commit()
    conn.close()

def find_item(item_key: str):
    for cat, items in MENU.items():
        if item_key in items:
            return cat, items[item_key]
    return None, None

# ================== MENU persistence ==================
def media_set(item_key: str, media_type: str, file_id: str | None):
    conn = db()
    cur = conn.cursor()
    now = utcnow().isoformat()

    if media_type == "photo":
        cur.execute("""
            INSERT INTO menu_media(item_key, photo_file_id, updated_at)
            VALUES(?, ?, ?)
            ON CONFLICT(item_key) DO UPDATE SET
                photo_file_id=excluded.photo_file_id,
                updated_at=excluded.updated_at
        """, (item_key, file_id, now))
    elif media_type == "video":
        cur.execute("""
            INSERT INTO menu_media(item_key, video_file_id, updated_at)
            VALUES(?, ?, ?)
            ON CONFLICT(item_key) DO UPDATE SET
                video_file_id=excluded.video_file_id,
                updated_at=excluded.updated_at
        """, (item_key, file_id, now))

    conn.commit()
    conn.close()

    _, item = find_item(item_key)
    if item:
        if media_type == "photo":
            item["photo_file_id"] = file_id
        else:
            item["video_file_id"] = file_id

def overrides_set(item_key: str, title=None, desc=None, price=None):
    conn = db()
    cur = conn.cursor()
    now = utcnow().isoformat()

    cur.execute("SELECT * FROM menu_overrides WHERE item_key=?", (item_key,))
    row = cur.fetchone()

    new_title = title if title is not None else (row["title"] if row else None)
    new_desc  = desc  if desc  is not None else (row["desc"]  if row else None)
    new_price = price if price is not None else (row["price"] if row else None)

    cur.execute("""
        INSERT INTO menu_overrides(item_key, title, desc, price, updated_at)
        VALUES(?,?,?,?,?)
        ON CONFLICT(item_key) DO UPDATE SET
            title=excluded.title,
            desc=excluded.desc,
            price=excluded.price,
            updated_at=excluded.updated_at
    """, (item_key, new_title, new_desc, new_price, now))

    conn.commit()
    conn.close()

    _, item = find_item(item_key)
    if item:
        if new_title:
            item["title"] = new_title
        if new_desc:
            item["desc"] = new_desc
        if new_price is not None:
            item["price"] = int(new_price)

def load_media_and_overrides():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT item_key, photo_file_id, video_file_id FROM menu_media")
    for r in cur.fetchall():
        _, item = find_item(r["item_key"])
        if item:
            item["photo_file_id"] = r["photo_file_id"]
            item["video_file_id"] = r["video_file_id"]

    cur.execute("SELECT item_key, title, desc, price FROM menu_overrides")
    for r in cur.fetchall():
        _, item = find_item(r["item_key"])
        if item:
            if r["title"]:
                item["title"] = r["title"]
            if r["desc"]:
                item["desc"] = r["desc"]
            if r["price"] is not None:
                item["price"] = int(r["price"])

    conn.close()

# ================== SCREEN SYSTEM ==================
def screen_text(chat_id: int, text: str, kb: InlineKeyboardMarkup):
    ui = get_ui(chat_id)
    mid = ui["main_message_id"] if ui else None
    kind = (ui["main_kind"] if ui else "text") or "text"

    if mid and kind != "text":
        safe_delete(chat_id, mid)
        mid = None

    if mid:
        try:
            bot.edit_message_text(text, chat_id, mid, reply_markup=kb, parse_mode="Markdown")
            return
        except Exception:
            safe_delete(chat_id, mid)

    msg = bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")
    set_ui_fields(chat_id, main_message_id=msg.message_id, main_kind="text")

def screen_photo(chat_id: int, photo_file_id: str, caption: str, kb: InlineKeyboardMarkup):
    ui = get_ui(chat_id)
    mid = ui["main_message_id"] if ui else None
    kind = (ui["main_kind"] if ui else "text") or "text"

    if mid and kind != "photo":
        safe_delete(chat_id, mid)
        mid = None

    if mid:
        try:
            bot.edit_message_caption(chat_id=chat_id, message_id=mid, caption=caption, reply_markup=kb, parse_mode="Markdown")
            return
        except Exception:
            safe_delete(chat_id, mid)

    msg = bot.send_photo(chat_id, photo_file_id, caption=caption, reply_markup=kb, parse_mode="Markdown")
    set_ui_fields(chat_id, main_message_id=msg.message_id, main_kind="photo")

# ================== KEYBOARDS ==================
def kb_home():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🌸 Signature ✧", callback_data="cat:Авторські Кальяни"),
        InlineKeyboardButton("🍊 Фруктові ✧", callback_data="cat:Фруктові Чаші"),
        InlineKeyboardButton("⚙️ Формат ✧", callback_data="cat:Формат"),
    )
    kb.row(
        InlineKeyboardButton("👤 Профіль ✧", callback_data="go:profile"),
        InlineKeyboardButton("⭐ Враження ✧", callback_data="go:feedback"),
    )
    kb.add(InlineKeyboardButton("📍 Бронювання ✧", url=BOOK_URL))
    return kb

def kb_back_home():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("← Назад", callback_data="go:home"),
        InlineKeyboardButton("👤 Профіль ✧", callback_data="go:profile"),
    )
    return kb

def kb_category(category: str):
    kb = InlineKeyboardMarkup()
    keys = list(MENU[category].keys())
    for i in range(0, len(keys), 2):
        row = []
        k1 = keys[i]
        row.append(InlineKeyboardButton(MENU[category][k1]["title"], callback_data=f"item:{k1}"))
        if i + 1 < len(keys):
            k2 = keys[i + 1]
            row.append(InlineKeyboardButton(MENU[category][k2]["title"], callback_data=f"item:{k2}"))
        kb.row(*row)
    kb.row(
        InlineKeyboardButton("← Назад", callback_data="go:home"),
        InlineKeyboardButton("⭐ Враження ✧", callback_data="go:feedback"),
    )
    return kb

def kb_item(item_key: str):
    cat, _ = find_item(item_key)
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("💾 Зберегти ✧", callback_data=f"fav:{item_key}"),
        InlineKeyboardButton("⭐ Оцінити ✧", callback_data=f"fb:hookah:{item_key}"),
    )
    kb.row(
        InlineKeyboardButton("← Повернутись", callback_data=f"cat:{cat}"),
        InlineKeyboardButton("🏠 На головну ✧", callback_data="go:home"),
    )
    return kb

def kb_feedback_root():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("💨 Кальян ✧", callback_data="fbroot:hookah"),
        InlineKeyboardButton("🤝 Сервіс ✧", callback_data="fbroot:service"),
    )
    kb.add(InlineKeyboardButton("← Назад", callback_data="go:home"))
    return kb

def kb_stars(kind: str, item_key: str | None):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("★", callback_data=f"rate:{kind}:{item_key or '-'}:1"),
        InlineKeyboardButton("★★", callback_data=f"rate:{kind}:{item_key or '-'}:2"),
        InlineKeyboardButton("★★★", callback_data=f"rate:{kind}:{item_key or '-'}:3"),
        InlineKeyboardButton("★★★★", callback_data=f"rate:{kind}:{item_key or '-'}:4"),
        InlineKeyboardButton("★★★★★", callback_data=f"rate:{kind}:{item_key or '-'}:5"),
    )
    kb.add(InlineKeyboardButton("Пропустити ✧", callback_data="skip_comment"))
    kb.add(InlineKeyboardButton("🏠 На головну ✧", callback_data="go:home"))
    return kb

def kb_fav_mix_actions(item_key: str):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("Пропустити ✧", callback_data="favmix:skip"),
        InlineKeyboardButton("Скинути ✧", callback_data="favmix:clear"),
    )
    kb.row(
        InlineKeyboardButton("← Повернутись", callback_data=f"item:{item_key}"),
        InlineKeyboardButton("🏠 На головну ✧", callback_data="go:home"),
    )
    return kb

def kb_admin_quick():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("👥 Users", callback_data="admin:users"),
        InlineKeyboardButton("📝 Last FB", callback_data="admin:lastfb"),
    )
    kb.row(
        InlineKeyboardButton("🔑 Keys", callback_data="admin:keys"),
        InlineKeyboardButton("📣 Help", callback_data="admin:help"),
    )
    kb.row(
        InlineKeyboardButton("✅ Admin ON", callback_data="adminmode:on"),
        InlineKeyboardButton("⛔ Admin OFF", callback_data="adminmode:off"),
    )
    return kb
def is_admin_user(message) -> bool:
    if ADMIN_ID <= 0:
        return False
    uid = getattr(message.from_user, "id", None)
    cid = getattr(message.chat, "id", None)
    return (uid == ADMIN_ID) or (cid == ADMIN_ID)

@bot.message_handler(commands=["whoami"])
def whoami_cmd(message):
    uid = getattr(message.from_user, "id", None)
    cid = getattr(message.chat, "id", None)
    bot.send_message(message.chat.id, f"from_user.id = `{uid}`\nchat.id = `{cid}`")

@bot.message_handler(commands=["admin"])
def admin_cmd(message):
    if not is_admin_user(message):
        return
    ensure_user(ADMIN_ID)
    mode = "ON ✅" if is_admin_mode(ADMIN_ID) else "OFF ⛔"
    admin_send(header("Admin") + f"Admin Mode: *{mode}*\n\nШвидкі дії:", kb_admin_quick())
# ================== SCREENS ==================
def render_home(chat_id: int):
    u = get_user(chat_id)
    status = (u["status"] or "Guest")
    visits = int(u["visits"] or 0)

    if status == "Black Edition":
        welcome = "🖤 Welcome back."
    elif status == "Signature Member":
        welcome = "🥂 Твій вечір починається тут."
    elif status == "Pink Insider":
        welcome = "🌸 Рожевий радий бачити тебе знову."
    else:
        welcome = "✨ Ласкаво просимо."

    fav_line = "—"
    fk = u["favorite_key"]
    fm = (u["favorite_mix"] or "").strip()
    if fk:
        _, it = find_item(fk)
        if it:
            fav_line = it["title"]
            if fm:
                fav_line = f"{fav_line}\n🧾 *Мікс:* _{fm}_"

    text = (
        header("Pink Lounge") +
        f"{welcome}\n\n"
        f"👑 *Статус:* {status}\n"
        f"📌 *Візити:* {visits}\n"
        f"💎 *Твій Signature:* {fav_line}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🍸 *Collection*\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    screen_text(chat_id, text, kb_home())

def render_category(chat_id: int, category: str):
    desc = CATEGORY_DESC.get(category, "")
    text = (
        header(category) +
        f"{desc}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✧ *Обери позицію* ✧\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    screen_text(chat_id, text, kb_category(category))

def render_item(chat_id: int, item_key: str):
    _, item = find_item(item_key)
    if not item:
        return render_home(chat_id)

    price = item.get("price")
    price_line = f"💳 *Ціна:* {price} грн\n\n" if price is not None else ""

    caption = (
        f"✧ *{item['title']}* ✧\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{price_line}"
        f"{item['desc']}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✧ *Дії* ✧\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    if item.get("photo_file_id"):
        screen_photo(chat_id, item["photo_file_id"], caption, kb_item(item_key))
    else:
        screen_text(chat_id, caption, kb_item(item_key))

def render_profile(chat_id: int):
    u = get_user(chat_id)
    status = (u["status"] or "Guest")
    visits = int(u["visits"] or 0)

    last = "—"
    if u["last_visit"]:
        dt = parse_iso(u["last_visit"])
        if dt:
            last = dt.strftime("%d.%m %H:%M")

    fav_line = "—"
    fk = u["favorite_key"]
    fm = (u["favorite_mix"] or "").strip()
    if fk:
        _, it = find_item(fk)
        if it:
            fav_line = it["title"]
            if fm:
                fav_line = f"{fav_line}\n🧾 *Мікс:* _{fm}_"

    text = (
        header("Профіль") +
        f"👑 *Статус:* {status}\n"
        f"📌 *Візити:* {visits}\n"
        f"🕰 *Останній візит:* {last}\n"
        f"💎 *Твій Signature:* {fav_line}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✧ *Personal Space* ✧\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    screen_text(chat_id, text, kb_back_home())

def render_feedback_root(chat_id: int):
    text = (
        header("Враження") +
        f"⭐ Оціни свій досвід.\n"
        f"Після зірок можеш написати коментар (до {COMMENT_MAX} символів) — *за бажанням*.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✧ *Що оцінюємо?* ✧\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    screen_text(chat_id, text, kb_feedback_root())

def render_rate(chat_id: int, kind: str, item_key: str | None):
    title = "💨 Кальян" if kind == "hookah" else "🤝 Сервіс"
    text = (
        header(title) +
        "Обери оцінку.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✧ *Рейтинг* ✧\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    screen_text(chat_id, text, kb_stars(kind, item_key))

def render_after_rating(chat_id: int):
    text = (
        header("Дякуємо") +
        f"✨ Якщо хочеш — напиши короткий коментар *до {COMMENT_MAX} символів*.\n"
        "Якщо ні — натисни *Пропустити ✧*.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✧ *Коментар* ✧\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Пропустити ✧", callback_data="skip_comment"))
    kb.add(InlineKeyboardButton("🏠 На головну ✧", callback_data="go:home"))
    screen_text(chat_id, text, kb)

def render_fav_mix_prompt(chat_id: int, item_key: str):
    _, item = find_item(item_key)
    if not item:
        return render_home(chat_id)

    text = (
        header("Улюблений мікс") +
        f"Ти обрав(ла): *{item['title']}*\n\n"
        f"✍️ Напиши свій мікс (до {COMMENT_MAX} символів).\n"
        "Наприклад:\n"
        "_Манго · груша · ківі_\n\n"
        "Якщо не хочеш — натисни *Пропустити ✧*."
    )
    screen_text(chat_id, text, kb_fav_mix_actions(item_key))

# ================== ADMIN HELP ==================
def list_keys_text():
    lines = [header("Menu Keys")]
    for cat, items in MENU.items():
        lines.append(f"*{cat}:*")
        for k in items.keys():
            lines.append(f"• `{k}`")
        lines.append("")
    return "\n".join(lines).strip()

def admin_help_text():
    return (
        header("Admin Help") +
        "Команди:\n"
        "• `/admin` — панель\n"
        "• `/adminmode on|off` — режим адміна\n"
        "• `/keys` — KEY позицій\n"
        "• `/setphoto KEY` — додати фото (фото/файл)\n"
        "• `/setvideo KEY` — додати відео (відео/файл)\n"
        "• `/delphoto KEY` — видалити фото\n"
        "• `/delvideo KEY` — видалити відео\n"
        "• `/setprice KEY 650` — ціна\n"
        "• `/settitle KEY Назва` — назва\n"
        "• `/setdesc KEY Опис...` — опис\n"
        "• `/broadcast текст` — розсилка\n"
        "• (media) caption: `broadcast:текст` — фото/відео розсилка\n"
    )

# ================== ADMIN STATE (DB) ==================
def admin_state_set(mode: str | None, item_key: str | None):
    conn = db()
    cur = conn.cursor()
    if not mode or not item_key:
        cur.execute("DELETE FROM admin_media_state WHERE admin_id=?", (ADMIN_ID,))
    else:
        cur.execute("""
            INSERT INTO admin_media_state(admin_id, mode, item_key, updated_at)
            VALUES(?,?,?,?)
            ON CONFLICT(admin_id) DO UPDATE SET
                mode=excluded.mode, item_key=excluded.item_key, updated_at=excluded.updated_at
        """, (ADMIN_ID, mode, item_key, utcnow().isoformat()))
    conn.commit()
    conn.close()

def admin_state_get():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admin_media_state WHERE admin_id=?", (ADMIN_ID,))
    r = cur.fetchone()
    conn.close()
    return r

def detect_doc_kind(document) -> str | None:
    fn = (document.file_name or "").lower()
    mt = (document.mime_type or "").lower()
    img_ext = (".jpg", ".jpeg", ".png", ".webp", ".heic")
    vid_ext = (".mp4", ".mov", ".m4v", ".webm")
    if mt.startswith("image/") or fn.endswith(img_ext):
        return "photo"
    if mt.startswith("video/") or fn.endswith(vid_ext):
        return "video"
    return None

def admin_send(text: str, kb=None):
    if ADMIN_ID <= 0:
        return None
    if not is_admin_mode(ADMIN_ID):
        ui = get_ui(ADMIN_ID)
        if ui:
            safe_delete(ADMIN_ID, ui["admin_message_id"])
    msg = bot.send_message(ADMIN_ID, text, reply_markup=kb, parse_mode="Markdown")
    if not is_admin_mode(ADMIN_ID):
        set_ui_fields(ADMIN_ID, admin_message_id=msg.message_id)
    return msg

# ================== COMMANDS ==================
@bot.message_handler(commands=["start", "menu"])
def start(message):
    chat_id = message.chat.id
    ensure_user(chat_id)

    try:
        tmp = bot.send_message(chat_id, "…", reply_markup=ReplyKeyboardRemove())
        safe_delete(chat_id, tmp.message_id)
    except Exception:
        pass

    parts = (message.text or "").split(maxsplit=1)
    start_param = parts[1].strip() if len(parts) > 1 else None

    table_code = extract_table_code(start_param)
    if table_code:
        try_checkin(chat_id, table_code)
        set_state(chat_id, 0, None, None, None)
        set_fav_mix_state(chat_id, 0, None)
        return render_home(chat_id)

    set_state(chat_id, 0, None, None, None)
    set_fav_mix_state(chat_id, 0, None)
    return render_home(chat_id)

@bot.message_handler(commands=["admin"])
def admin_cmd(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    ensure_user(ADMIN_ID)
    mode = "ON ✅" if is_admin_mode(ADMIN_ID) else "OFF ⛔"
    admin_send(header("Admin") + f"Admin Mode: *{mode}*\n\nШвидкі дії:", kb_admin_quick())

@bot.message_handler(commands=["adminmode"])
def adminmode_cmd(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        admin_send("Формат: `/adminmode on` або `/adminmode off`")
        return
    v = parts[1].strip().lower()
    set_admin_mode(ADMIN_ID, 1 if v in ("on", "1", "true", "yes") else 0)
    mode = "ON ✅" if is_admin_mode(ADMIN_ID) else "OFF ⛔"
    admin_send(f"Готово. Admin Mode: *{mode}*", kb_admin_quick())

@bot.message_handler(commands=["keys"])
def keys_cmd(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    admin_send(list_keys_text(), kb_admin_quick())

@bot.message_handler(commands=["setphoto"])
def setphoto_cmd(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        admin_send("Формат: `/setphoto SIGNATURE_TROPICAL`")
        return
    key = parts[1].strip()
    cat, item = find_item(key)
    if not item:
        admin_send("Не знайшов KEY. Натисни `/keys`.")
        return
    admin_state_set("setphoto", key)
    admin_send(f"✅ Надішли *фото* (як фото або файл) для:\n{cat} → {item['title']}")

@bot.message_handler(commands=["setvideo"])
def setvideo_cmd(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        admin_send("Формат: `/setvideo SIGNATURE_TROPICAL`")
        return
    key = parts[1].strip()
    cat, item = find_item(key)
    if not item:
        admin_send("Не знайшов KEY. Натисни `/keys`.")
        return
    admin_state_set("setvideo", key)
    admin_send(f"✅ Надішли *відео* (як відео або файл) для:\n{cat} → {item['title']}")

@bot.message_handler(commands=["delphoto"])
def delphoto_cmd(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        admin_send("Формат: `/delphoto KEY`")
        return
    key = parts[1].strip()
    if not find_item(key)[1]:
        admin_send("Не знайшов KEY. `/keys`")
        return
    media_set(key, "photo", None)
    admin_send(f"✅ Фото видалено для `{key}`")

@bot.message_handler(commands=["delvideo"])
def delvideo_cmd(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        admin_send("Формат: `/delvideo KEY`")
        return
    key = parts[1].strip()
    if not find_item(key)[1]:
        admin_send("Не знайшов KEY. `/keys`")
        return
    media_set(key, "video", None)
    admin_send(f"✅ Відео видалено для `{key}`")

@bot.message_handler(commands=["setprice"])
def setprice_cmd(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        admin_send("Формат: `/setprice KEY 650`")
        return
    key = parts[1].strip()
    if not find_item(key)[1]:
        admin_send("Не знайшов KEY. `/keys`")
        return
    try:
        price = int(parts[2].strip())
        if price < 0:
            raise ValueError
    except Exception:
        admin_send("Ціна має бути числом (наприклад 650).")
        return
    overrides_set(key, price=price)
    admin_send(f"✅ Ціну оновлено: `{key}` → *{price} грн*")

@bot.message_handler(commands=["settitle"])
def settitle_cmd(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        admin_send("Формат: `/settitle KEY Нова назва`")
        return
    key = parts[1].strip()
    if not find_item(key)[1]:
        admin_send("Не знайшов KEY. `/keys`")
        return
    overrides_set(key, title=parts[2].strip())
    admin_send(f"✅ Назву оновлено: `{key}`")

@bot.message_handler(commands=["setdesc"])
def setdesc_cmd(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        admin_send("Формат: `/setdesc KEY Опис...`")
        return
    key = parts[1].strip()
    if not find_item(key)[1]:
        admin_send("Не знайшов KEY. `/keys`")
        return
    overrides_set(key, desc=parts[2].strip())
    admin_send(f"✅ Опис оновлено: `{key}`")

@bot.message_handler(commands=["broadcast"])
def broadcast_text(message):
    if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
        return
    text = (message.text or "").replace("/broadcast", "").strip()
    if not text:
        admin_send("Формат: `/broadcast Текст`")
        return

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM users")
    users = [int(r["chat_id"]) for r in cur.fetchall()]
    conn.close()

    ok = 0
    for uid in users:
        try:
            bot.send_message(uid, text)
            ok += 1
            time.sleep(0.05)
        except Exception:
            pass
    admin_send(f"✅ Розсилка: {ok}/{len(users)}")

# ================== MEDIA HANDLER ==================
@bot.message_handler(content_types=["photo", "video", "document"])
def media_router(message):
    try:
        if ADMIN_ID <= 0 or message.from_user.id != ADMIN_ID:
            return

        caption = (message.caption or "").strip()

        kind = None
        file_id = None

        if message.content_type == "photo":
            kind = "photo"
            file_id = message.photo[-1].file_id
        elif message.content_type == "video":
            kind = "video"
            file_id = message.video.file_id
        elif message.content_type == "document":
            kind = detect_doc_kind(message.document)
            if kind:
                file_id = message.document.file_id
            else:
                return

        st = admin_state_get()
        if st:
            key = st["item_key"]
            mode = st["mode"]

            if mode == "setphoto" and kind == "photo":
                admin_state_set(None, None)
                if find_item(key)[1]:
                    media_set(key, "photo", file_id)
                    admin_send(f"✅ Фото привʼязано для `{key}`")
                else:
                    admin_send("❗️KEY не знайдено. `/keys`")
                return

            if mode == "setvideo" and kind == "video":
                admin_state_set(None, None)
                if find_item(key)[1]:
                    media_set(key, "video", file_id)
                    admin_send(f"✅ Відео привʼязано для `{key}`")
                else:
                    admin_send("❗️KEY не знайдено. `/keys`")
                return

        if caption.lower().startswith("broadcast:"):
            text = caption[len("broadcast:"):].strip() or "🌸 Pink Lounge"

            conn = db()
            cur = conn.cursor()
            cur.execute("SELECT chat_id FROM users")
            users = [int(r["chat_id"]) for r in cur.fetchall()]
            conn.close()

            ok = 0
            for uid in users:
                try:
                    if kind == "photo":
                        bot.send_photo(uid, file_id, caption=text)
                    else:
                        bot.send_video(uid, file_id, caption=text)
                    ok += 1
                    time.sleep(0.08 if kind == "video" else 0.06)
                except Exception:
                    pass
            admin_send(f"✅ {('Відео' if kind=='video' else 'Фото')}-розсилка: {ok}/{len(users)}")
            return

    except Exception:
        print("❌ MEDIA CRASH:\n", traceback.format_exc())

# ================== CALLBACKS (ANTI-CRASH) ==================
@bot.callback_query_handler(func=lambda c: True)
def on_callback(call):
    try:
        chat_id = call.message.chat.id if call.message else call.from_user.id
        data = call.data or ""

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        ensure_user(chat_id)

        if data.startswith(("go:", "cat:", "item:", "fav:", "fb", "rate:", "admin:", "adminmode:", "favmix:")) or data in ("skip_comment",):
            typing(chat_id)

        if data == "go:home":
            set_state(chat_id, 0, None, None, None)
            set_fav_mix_state(chat_id, 0, None)
            return render_home(chat_id)

        if data.startswith("cat:"):
            category = data.split("cat:", 1)[1]
            if category in MENU:
                set_state(chat_id, 0, None, None, None)
                set_fav_mix_state(chat_id, 0, None)
                return render_category(chat_id, category)
            return render_home(chat_id)

        if data.startswith("item:"):
            key = data.split("item:", 1)[1]
            set_state(chat_id, 0, None, None, None)
            set_fav_mix_state(chat_id, 0, None)
            return render_item(chat_id, key)

        if data == "go:profile":
            set_state(chat_id, 0, None, None, None)
            set_fav_mix_state(chat_id, 0, None)
            return render_profile(chat_id)

        if data == "go:feedback":
            set_state(chat_id, 0, None, None, None)
            set_fav_mix_state(chat_id, 0, None)
            return render_feedback_root(chat_id)

        # favorite flow
        if data.startswith("fav:"):
            key = data.split("fav:", 1)[1]
            set_state(chat_id, 0, None, None, None)
            set_fav_mix_state(chat_id, 1, key)
            return render_fav_mix_prompt(chat_id, key)

        if data == "favmix:skip":
            st = get_state(chat_id)
            key = (st["pending_fav_item_key"] if st else None)
            if key:
                set_favorite_mix(chat_id, key, None)
            set_fav_mix_state(chat_id, 0, None)
            return render_home(chat_id)

        if data == "favmix:clear":
            clear_favorite(chat_id)
            set_fav_mix_state(chat_id, 0, None)
            return render_home(chat_id)

        # feedback
        if data.startswith("fbroot:"):
            kind = data.split("fbroot:", 1)[1]
            if kind == "service":
                return render_rate(chat_id, "service", None)

            txt = (
                header("💨 Кальян") +
                "Щоб оцінити кальян — відкрий позицію в меню\n"
                "і натисни *⭐ Оцінити ✧*.\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "✧ *Меню* ✧\n"
                "━━━━━━━━━━━━━━━━━━"
            )
            kb = InlineKeyboardMarkup()
            kb.row(
                InlineKeyboardButton("🌸 Signature ✧", callback_data="cat:Авторські Кальяни"),
                InlineKeyboardButton("🍊 Фруктові ✧", callback_data="cat:Фруктові Чаші"),
                InlineKeyboardButton("⚙️ Формат ✧", callback_data="cat:Формат"),
            )
            kb.add(InlineKeyboardButton("← Назад", callback_data="go:feedback"))
            return screen_text(chat_id, txt, kb)

        if data.startswith("fb:"):
            _, kind, item_key = data.split(":", 2)
            return render_rate(chat_id, kind, item_key)

        if data.startswith("rate:"):
            _, kind, item_raw, stars_raw = data.split(":", 3)
            item_key = None if item_raw == "-" else item_raw
            rating = int(stars_raw)
            set_fav_mix_state(chat_id, 0, None)
            set_state(chat_id, 1, kind, item_key, rating)
            return render_after_rating(chat_id)

        if data == "skip_comment":
            st = get_state(chat_id)
            if st and int(st["awaiting_comment"] or 0) == 1:
                add_feedback(chat_id, st["pending_kind"], int(st["pending_rating"]), st["pending_item_key"], None)
            set_state(chat_id, 0, None, None, None)
            return render_home(chat_id)

        # admin callbacks
        if ADMIN_ID > 0 and chat_id == ADMIN_ID and data.startswith("adminmode:"):
            v = data.split("adminmode:", 1)[1]
            set_admin_mode(ADMIN_ID, 1 if v == "on" else 0)
            mode = "ON ✅" if is_admin_mode(ADMIN_ID) else "OFF ⛔"
            admin_send(f"Admin Mode: *{mode}*", kb_admin_quick())
            return

        if ADMIN_ID > 0 and chat_id == ADMIN_ID and data.startswith("admin:"):
            if data == "admin:users":
                conn = db()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) as c FROM users")
                c = cur.fetchone()["c"]
                conn.close()
                admin_send(header("Admin") + f"👥 Користувачів: *{c}*", kb_admin_quick())
                return

            if data == "admin:keys":
                admin_send(list_keys_text(), kb_admin_quick())
                return

            if data == "admin:help":
                admin_send(admin_help_text(), kb_admin_quick())
                return

        return render_home(chat_id)

    except Exception:
        print("❌ CALLBACK CRASH:\n", traceback.format_exc())
        try:
            chat_id = call.message.chat.id if call.message else call.from_user.id
            return render_home(chat_id)
        except Exception:
            pass

# ================== TEXT HANDLER (ANTI-CRASH) ==================
@bot.message_handler(func=lambda m: True)
def on_text(message):
    try:
        chat_id = message.chat.id
        ensure_user(chat_id)

        txt = (message.text or "").strip()

        if txt.startswith("/"):
            return

        if ADMIN_ID > 0 and message.from_user.id == ADMIN_ID and is_admin_mode(ADMIN_ID):
            return

        st = get_state(chat_id)

        if st and int(st["awaiting_fav_mix"] or 0) == 1:
            key = st["pending_fav_item_key"]
            mix = (txt[:COMMENT_MAX]).strip()
            if key:
                set_favorite_mix(chat_id, key, mix or None)
            set_fav_mix_state(chat_id, 0, None)
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass
            typing(chat_id)
            return render_home(chat_id)

        if st and int(st["awaiting_comment"] or 0) == 1:
            comment = (txt[:COMMENT_MAX]).strip()
            add_feedback(chat_id, st["pending_kind"], int(st["pending_rating"]), st["pending_item_key"], comment or None)
            set_state(chat_id, 0, None, None, None)
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass
            typing(chat_id)
            return render_home(chat_id)

        table_code = extract_table_code(txt)
        if table_code:
            try_checkin(chat_id, table_code)
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass
            typing(chat_id)
            return render_home(chat_id)

        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

        typing(chat_id)
        return render_home(chat_id)

    except Exception:
        print("❌ TEXT CRASH:\n", traceback.format_exc())
        try:
            ensure_user(message.chat.id)
            return render_home(message.chat.id)
        except Exception:
            pass

# ================== RUN ==================
def start_bot():
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception:
        pass

    init_db()
    migrate_db()
    if ADMIN_ID > 0:
        ensure_user(ADMIN_ID)
    load_media_and_overrides()

    print("Bot is running...")
    bot.polling(none_stop=True, interval=0, timeout=30, long_polling_timeout=30)

if __name__ == "__main__":
    start_bot()



# bot.py — Pink Lounge Bot (stable, Railway-ready)
# Required Railway Variables:
#   BOT_TOKEN = 123456:ABC...
#   ADMIN_ID  = 641359493

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
TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
ADMIN_ID_RAW = (os.getenv("ADMIN_ID") or "").strip()

if not TOKEN or ":" not in TOKEN:
    raise RuntimeError("❌ BOT_TOKEN missing/invalid. Set Railway Variable BOT_TOKEN")
if not ADMIN_ID_RAW.isdigit():
    raise RuntimeError("❌ ADMIN_ID missing. Set Railway Variable ADMIN_ID (number)")

ADMIN_ID = int(ADMIN_ID_RAW)

BOOK_URL = (os.getenv("BOOK_URL") or "https://www.instagram.com/rozhevyi.sushi.lounge/").strip()
DB_FILE = (os.getenv("DB_FILE") or "pink_lounge.db").strip()

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
apihelper.CONNECT_TIMEOUT = 10
apihelper.READ_TIMEOUT = 30

# ================== CONSTANTS ==================
ANIM_DELAY = 0.12
COMMENT_MAX = 100
FAV_MIX_MAX = 70
VISIT_COOLDOWN_HOURS = 24


# ================== SAFE TELEGRAM HELPERS ==================
def _strip_md(text: str) -> str:
    # removes most markdown specials to avoid "can't parse entities"
    return re.sub(r"[*_`[\]()~>#+=|{}.!\\-]", " ", text)

def log_exc(where: str, e: Exception):
    print(f"\n=== ERROR in {where} ===")
    print(str(e))
    print(traceback.format_exc())
    print("=== /ERROR ===\n")

def safe_send_message(chat_id: int, text: str, reply_markup=None, parse_mode="Markdown"):
    try:
        return bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            return bot.send_message(chat_id, _strip_md(text), reply_markup=reply_markup)
        except Exception as e:
            log_exc("safe_send_message", e)
            return None

def safe_edit_message_text(chat_id: int, message_id: int, text: str, reply_markup=None, parse_mode="Markdown") -> bool:
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, parse_mode=parse_mode)
        return True
    except Exception as e:
        s = str(e).lower()
        if "message is not modified" in s:
            return True
        try:
            bot.edit_message_text(_strip_md(text), chat_id, message_id, reply_markup=reply_markup)
            return True
        except Exception as e2:
            s2 = str(e2).lower()
            if "message is not modified" in s2:
                return True
            return False

def safe_edit_caption(chat_id: int, message_id: int, caption: str, reply_markup=None, parse_mode="Markdown") -> bool:
    try:
        bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)
        return True
    except Exception as e:
        s = str(e).lower()
        if "message is not modified" in s:
            return True
        try:
            bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=_strip_md(caption), reply_markup=reply_markup)
            return True
        except Exception:
            return False

def safe_send_photo(chat_id: int, file_id: str, caption: str, reply_markup=None, parse_mode="Markdown"):
    try:
        return bot.send_photo(chat_id, file_id, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            return bot.send_photo(chat_id, file_id, caption=_strip_md(caption), reply_markup=reply_markup)
        except Exception as e:
            log_exc("safe_send_photo", e)
            return None

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

def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def header(title: str) -> str:
    return f"✧ *{title}* ✧\n━━━━━━━━━━━━━━━━━━\n"


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
            "price": 650,
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
            "price": 650,
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
            "price": 450,
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
            "price": 450,
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
            "price": 450,
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
            pending_kind TEXT,
            pending_item_key TEXT,
            pending_rating INTEGER,
            awaiting_fav_mix INTEGER DEFAULT 0,
            pending_fav_key TEXT
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
    if not _column_exists(cur, "state", "pending_fav_key"):
        cur.execute("ALTER TABLE state ADD COLUMN pending_fav_key TEXT")

    conn.commit()
    conn.close()

def ensure_user(chat_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users(chat_id, created_at) VALUES(?, ?)", (chat_id, utcnow().isoformat()))
    cur.execute("""
        INSERT OR IGNORE INTO state(chat_id, awaiting_comment, awaiting_fav_mix)
        VALUES(?, 0, 0)
    """, (chat_id,))
    cur.execute("INSERT OR IGNORE INTO settings(chat_id, admin_mode) VALUES(?, 0)", (ADMIN_ID,))  # store admin settings on admin id
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

def set_state_feedback(chat_id: int, awaiting: int, kind=None, item_key=None, rating=None):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE state
        SET awaiting_comment=?, pending_kind=?, pending_item_key=?, pending_rating=?
        WHERE chat_id=?
    """, (awaiting, kind, item_key, rating, chat_id))
    conn.commit()
    conn.close()

def set_state_favorite(chat_id: int, awaiting_fav: int, fav_key: str | None):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE state
        SET awaiting_fav_mix=?, pending_fav_key=?
        WHERE chat_id=?
    """, (awaiting_fav, fav_key, chat_id))
    conn.commit()
    conn.close()

def clear_all_state(chat_id: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE state
        SET awaiting_comment=0, pending_kind=NULL, pending_item_key=NULL, pending_rating=NULL,
            awaiting_fav_mix=0, pending_fav_key=NULL
        WHERE chat_id=?
    """, (chat_id,))
    conn.commit()
    conn.close()

def is_admin_mode() -> bool:
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT admin_mode FROM settings WHERE chat_id=?", (ADMIN_ID,))
    r = cur.fetchone()
    conn.close()
    return bool(r and int(r["admin_mode"] or 0) == 1)

def set_admin_mode(val: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings(chat_id, admin_mode)
        VALUES(?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET admin_mode=excluded.admin_mode
    """, (ADMIN_ID, val))
    conn.commit()
    conn.close()

def status_from_visits(v: int) -> str:
    if v >= 60: return "Black Edition"
    if v >= 30: return "Signature Member"
    if v >= 10: return "Pink Insider"
    return "Guest"

def try_checkin(chat_id: int, table_code: str | None) -> bool:
    u = get_user(chat_id)
    now = utcnow()

    if u and u["last_visit"]:
        try:
            last = datetime.fromisoformat(u["last_visit"])
            if now - last < timedelta(hours=VISIT_COOLDOWN_HOURS):
                return False
        except Exception:
            pass

    visits = int(u["visits"] or 0) + 1
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

def set_favorite(chat_id: int, item_key: str, mix_text: str | None):
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET favorite_key=?, favorite_mix=? WHERE chat_id=?", (item_key, mix_text, chat_id))
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


# ================== UI SCREENS ==================
def screen_text(chat_id: int, text: str, kb: InlineKeyboardMarkup):
    ui = get_ui(chat_id)
    mid = ui["main_message_id"] if ui else None
    kind = (ui["main_kind"] if ui else "text") or "text"

    if mid and kind != "text":
        safe_delete(chat_id, mid)
        mid = None

    if mid:
        if safe_edit_message_text(chat_id, mid, text, reply_markup=kb, parse_mode="Markdown"):
            return
        safe_delete(chat_id, mid)

    msg = safe_send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")
    if msg:
        set_ui_fields(chat_id, main_message_id=msg.message_id, main_kind="text")

def screen_photo(chat_id: int, photo_file_id: str, caption: str, kb: InlineKeyboardMarkup):
    ui = get_ui(chat_id)
    mid = ui["main_message_id"] if ui else None
    kind = (ui["main_kind"] if ui else "text") or "text"

    if mid and kind != "photo":
        safe_delete(chat_id, mid)
        mid = None

    if mid:
        if safe_edit_caption(chat_id, mid, caption, reply_markup=kb, parse_mode="Markdown"):
            return
        safe_delete(chat_id, mid)

    msg = safe_send_photo(chat_id, photo_file_id, caption, reply_markup=kb, parse_mode="Markdown")
    if msg:
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
        InlineKeyboardButton("💾 Улюблений ✧", callback_data=f"favask:{item_key}"),
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


# ================== RENDER ==================
def _favorite_display(u):
    fk = u["favorite_key"] if u else None
    fm = u["favorite_mix"] if u else None
    if not fk:
        return "—"
    _, it = find_item(fk)
    title = it["title"] if it else fk
    return f"{title}\n`{fm}`" if fm else title

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

    text = (
        header("Pink Lounge") +
        f"{welcome}\n\n"
        f"👑 *Статус:* {status}\n"
        f"📌 *Візити:* {visits}\n"
        f"💎 *Твій фаворит:* {_favorite_display(u)}\n\n"
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
        try:
            last_dt = datetime.fromisoformat(u["last_visit"])
            last = last_dt.strftime("%d.%m %H:%M")
        except Exception:
            pass

    text = (
        header("Профіль") +
        f"👑 *Статус:* {status}\n"
        f"📌 *Візити:* {visits}\n"
        f"🕰 *Останній візит:* {last}\n"
        f"💎 *Твій фаворит:* {_favorite_display(u)}\n\n"
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

def render_ask_fav_mix(chat_id: int, item_key: str):
    _, item = find_item(item_key)
    title = item["title"] if item else item_key
    text = (
        header("Улюблений") +
        f"Ти обрав(ла): *{title}*\n\n"
        f"Тепер *впиши свій мікс/побажання* (до {FAV_MIX_MAX} символів).\n"
        "Наприклад: `манго · груша · ківі` або `мʼяко, без холоду`.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✧ *Твій мікс* ✧\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Пропустити (без міксу) ✧", callback_data="favmix:skip"))
    kb.add(InlineKeyboardButton("🏠 На головну ✧", callback_data="go:home"))
    screen_text(chat_id, text, kb)


# ================== ADMIN ==================
admin_state = {}  # {"mode": "setphoto"/"setvideo", "key": "..."}

def is_admin_message(message) -> bool:
    try:
        return int(getattr(message.from_user, "id", 0)) == ADMIN_ID
    except Exception:
        return False

def admin_send(chat_id: int, text: str, kb=None):
    # always send to same chat to avoid 403 DM issues
    safe_send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

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


# ================== COMMANDS ==================
@bot.message_handler(commands=["start", "menu"])
def cmd_start(message):
    try:
        chat_id = message.chat.id
        ensure_user(chat_id)

        try:
            tmp = safe_send_message(chat_id, "…", reply_markup=ReplyKeyboardRemove())
            if tmp:
                safe_delete(chat_id, tmp.message_id)
        except Exception:
            pass

        parts = (message.text or "").split(maxsplit=1)
        start_param = parts[1].strip() if len(parts) > 1 else None

        # QR check-in: /start t12
        if start_param and start_param.lower().startswith("t") and start_param[1:].isdigit():
            try_checkin(chat_id, start_param.lower())
            clear_all_state(chat_id)
            return render_home(chat_id)

        clear_all_state(chat_id)
        return render_home(chat_id)
    except Exception as e:
        log_exc("cmd_start", e)

@bot.message_handler(commands=["admin"])
def admin_cmd(message):
    try:
        if not is_admin_message(message):
            return
        ensure_user(message.chat.id)
        mode = "ON ✅" if is_admin_mode() else "OFF ⛔"
        admin_send(message.chat.id, header("Admin") + f"Admin Mode: *{mode}*\n\nШвидкі дії:", kb_admin_quick())
    except Exception as e:
        log_exc("admin_cmd", e)

@bot.message_handler(commands=["adminmode"])
def adminmode_cmd(message):
    try:
        if not is_admin_message(message):
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            admin_send(message.chat.id, "Формат: `/adminmode on` або `/adminmode off`")
            return
        v = parts[1].strip().lower()
        set_admin_mode(1 if v in ("on", "1", "true", "yes") else 0)
        mode = "ON ✅" if is_admin_mode() else "OFF ⛔"
        admin_send(message.chat.id, f"Готово. Admin Mode: *{mode}*", kb_admin_quick())
    except Exception as e:
        log_exc("adminmode_cmd", e)

@bot.message_handler(commands=["keys"])
def keys_cmd(message):
    try:
        if not is_admin_message(message):
            return
        admin_send(message.chat.id, list_keys_text(), kb_admin_quick())
    except Exception as e:
        log_exc("keys_cmd", e)

@bot.message_handler(commands=["setphoto"])
def setphoto_cmd(message):
    try:
        if not is_admin_message(message):
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            admin_send(message.chat.id, "Формат: `/setphoto SIGNATURE_TROPICAL`")
            return
        key = parts[1].strip()
        cat, item = find_item(key)
        if not item:
            admin_send(message.chat.id, "Не знайшов KEY. Натисни `/keys`.")
            return
        admin_state["mode"] = "setphoto"
        admin_state["key"] = key
        admin_send(message.chat.id, f"✅ Надішли *фото* (як фото або файл) для:\n{cat} → {item['title']}")
    except Exception as e:
        log_exc("setphoto_cmd", e)

@bot.message_handler(commands=["setvideo"])
def setvideo_cmd(message):
    try:
        if not is_admin_message(message):
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            admin_send(message.chat.id, "Формат: `/setvideo SIGNATURE_TROPICAL`")
            return
        key = parts[1].strip()
        cat, item = find_item(key)
        if not item:
            admin_send(message.chat.id, "Не знайшов KEY. Натисни `/keys`.")
            return
        admin_state["mode"] = "setvideo"
        admin_state["key"] = key
        admin_send(message.chat.id, f"✅ Надішли *відео* (як відео або файл) для:\n{cat} → {item['title']}")
    except Exception as e:
        log_exc("setvideo_cmd", e)

@bot.message_handler(commands=["delphoto"])
def delphoto_cmd(message):
    try:
        if not is_admin_message(message):
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            admin_send(message.chat.id, "Формат: `/delphoto KEY`")
            return
        key = parts[1].strip()
        if not find_item(key)[1]:
            admin_send(message.chat.id, "Не знайшов KEY. `/keys`")
            return
        media_set(key, "photo", None)
        admin_send(message.chat.id, f"✅ Фото видалено для `{key}`", kb_admin_quick())
    except Exception as e:
        log_exc("delphoto_cmd", e)

@bot.message_handler(commands=["delvideo"])
def delvideo_cmd(message):
    try:
        if not is_admin_message(message):
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            admin_send(message.chat.id, "Формат: `/delvideo KEY`")
            return
        key = parts[1].strip()
        if not find_item(key)[1]:
            admin_send(message.chat.id, "Не знайшов KEY. `/keys`")
            return
        media_set(key, "video", None)
        admin_send(message.chat.id, f"✅ Відео видалено для `{key}`", kb_admin_quick())
    except Exception as e:
        log_exc("delvideo_cmd", e)

@bot.message_handler(commands=["setprice"])
def setprice_cmd(message):
    try:
        if not is_admin_message(message):
            return
        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 3:
            admin_send(message.chat.id, "Формат: `/setprice KEY 650`")
            return
        key = parts[1].strip()
        if not find_item(key)[1]:
            admin_send(message.chat.id, "Не знайшов KEY. `/keys`")
            return
        try:
            price = int(parts[2].strip())
            if price < 0:
                raise ValueError
        except Exception:
            admin_send(message.chat.id, "Ціна має бути числом (наприклад 650).")
            return
        overrides_set(key, price=price)
        admin_send(message.chat.id, f"✅ Ціну оновлено: `{key}` → *{price} грн*", kb_admin_quick())
    except Exception as e:
        log_exc("setprice_cmd", e)

@bot.message_handler(commands=["settitle"])
def settitle_cmd(message):
    try:
        if not is_admin_message(message):
            return
        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 3:
            admin_send(message.chat.id, "Формат: `/settitle KEY Нова назва`")
            return
        key = parts[1].strip()
        if not find_item(key)[1]:
            admin_send(message.chat.id, "Не знайшов KEY. `/keys`")
            return
        overrides_set(key, title=parts[2].strip())
        admin_send(message.chat.id, f"✅ Назву оновлено: `{key}`", kb_admin_quick())
    except Exception as e:
        log_exc("settitle_cmd", e)

@bot.message_handler(commands=["setdesc"])
def setdesc_cmd(message):
    try:
        if not is_admin_message(message):
            return
        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 3:
            admin_send(message.chat.id, "Формат: `/setdesc KEY Опис...`")
            return
        key = parts[1].strip()
        if not find_item(key)[1]:
            admin_send(message.chat.id, "Не знайшов KEY. `/keys`")
            return
        overrides_set(key, desc=parts[2].strip())
        admin_send(message.chat.id, f"✅ Опис оновлено: `{key}`", kb_admin_quick())
    except Exception as e:
        log_exc("setdesc_cmd", e)

@bot.message_handler(commands=["broadcast"])
def broadcast_text(message):
    try:
        if not is_admin_message(message):
            return
        text = (message.text or "").replace("/broadcast", "", 1).strip()
        if not text:
            admin_send(message.chat.id, "Формат: `/broadcast Текст`")
            return

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM users")
        users = [int(r["chat_id"]) for r in cur.fetchall()]
        conn.close()

        ok = 0
        for uid in users:
            try:
                safe_send_message(uid, text)
                ok += 1
                time.sleep(0.05)
            except Exception:
                pass

        admin_send(message.chat.id, f"✅ Розсилка: {ok}/{len(users)}", kb_admin_quick())
    except Exception as e:
        log_exc("broadcast_text", e)

@bot.message_handler(content_types=["photo", "video", "document"])
def media_router(message):
    try:
        if not is_admin_message(message):
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

        st_mode = admin_state.get("mode")
        st_key = admin_state.get("key")

        if st_mode and st_key:
            if st_mode == "setphoto" and kind == "photo":
                admin_state.clear()
                if find_item(st_key)[1]:
                    media_set(st_key, "photo", file_id)
                    admin_send(message.chat.id, f"✅ Фото привʼязано для `{st_key}`", kb_admin_quick())
                else:
                    admin_send(message.chat.id, "❗️KEY не знайдено. `/keys`", kb_admin_quick())
                return

            if st_mode == "setvideo" and kind == "video":
                admin_state.clear()
                if find_item(st_key)[1]:
                    media_set(st_key, "video", file_id)
                    admin_send(message.chat.id, f"✅ Відео привʼязано для `{st_key}`", kb_admin_quick())
                else:
                    admin_send(message.chat.id, "❗️KEY не знайдено. `/keys`", kb_admin_quick())
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
                        safe_send_photo(uid, file_id, text)
                    else:
                        bot.send_video(uid, file_id, caption=text)  # video caption usually ok
                    ok += 1
                    time.sleep(0.08 if kind == "video" else 0.06)
                except Exception:
                    pass

            admin_send(message.chat.id, f"✅ {('Відео' if kind=='video' else 'Фото')}-розсилка: {ok}/{len(users)}", kb_admin_quick())
            return

    except Exception as e:
        log_exc("media_router", e)


# ================== CALLBACKS ==================
@bot.callback_query_handler(func=lambda c: True)
def on_callback(call):
    try:
        chat_id = call.message.chat.id
        data = call.data or ""

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        ensure_user(chat_id)

        if data.startswith(("go:", "cat:", "item:", "favask:", "favmix:", "fb", "rate:", "admin:", "adminmode:", "skip_comment")):
            typing(chat_id)

        if data == "go:home":
            clear_all_state(chat_id)
            return render_home(chat_id)

        if data.startswith("cat:"):
            category = data.split("cat:", 1)[1]
            if category in MENU:
                clear_all_state(chat_id)
                return render_category(chat_id, category)
            return render_home(chat_id)

        if data.startswith("item:"):
            key = data.split("item:", 1)[1]
            clear_all_state(chat_id)
            return render_item(chat_id, key)

        if data == "go:profile":
            clear_all_state(chat_id)
            return render_profile(chat_id)

        if data == "go:feedback":
            clear_all_state(chat_id)
            return render_feedback_root(chat_id)

        # Favorite flow
        if data.startswith("favask:"):
            key = data.split("favask:", 1)[1]
            if not find_item(key)[1]:
                return render_home(chat_id)
            set_state_favorite(chat_id, 1, key)
            return render_ask_fav_mix(chat_id, key)

        if data == "favmix:skip":
            st = get_state(chat_id)
            key = st["pending_fav_key"] if st else None
            if key and find_item(key)[1]:
                set_favorite(chat_id, key, None)
            set_state_favorite(chat_id, 0, None)
            return render_home(chat_id)

        # Feedback
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
            set_state_feedback(chat_id, 1, kind, item_key, rating)
            return render_after_rating(chat_id)

        if data == "skip_comment":
            st = get_state(chat_id)
            if st and int(st["awaiting_comment"] or 0) == 1:
                add_feedback(chat_id, st["pending_kind"], int(st["pending_rating"]), st["pending_item_key"], None)
            set_state_feedback(chat_id, 0, None, None, None)
            return render_home(chat_id)

        # ================== ADMIN CALLBACKS (fixed) ==================
        if int(getattr(call.from_user, "id", 0)) == ADMIN_ID and data.startswith("adminmode:"):
            v = data.split("adminmode:", 1)[1]
            set_admin_mode(1 if v == "on" else 0)
            mode = "ON ✅" if is_admin_mode() else "OFF ⛔"
            admin_send(chat_id, f"Admin Mode: *{mode}*", kb_admin_quick())
            return

        if int(getattr(call.from_user, "id", 0)) == ADMIN_ID and data.startswith("admin:"):
            if data == "admin:users":
                conn = db()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) as c FROM users")
                c = cur.fetchone()["c"]
                conn.close()
                admin_send(chat_id, header("Admin") + f"👥 Користувачів: *{c}*", kb_admin_quick())
                return

            if data == "admin:keys":
                admin_send(chat_id, list_keys_text(), kb_admin_quick())
                return

            if data == "admin:help":
                admin_send(chat_id, admin_help_text(), kb_admin_quick())
                return

            if data == "admin:lastfb":
                conn = db()
                cur = conn.cursor()
                cur.execute("SELECT * FROM feedback ORDER BY id DESC LIMIT 1")
                r = cur.fetchone()
                conn.close()
                if not r:
                    admin_send(chat_id, header("Last FB") + "Немає відгуків.", kb_admin_quick())
                    return
                txt = (
                    header("Last FB") +
                    f"chat_id: `{r['chat_id']}`\n"
                    f"kind: `{r['kind']}`\n"
                    f"item_key: `{r['item_key'] or '-'}`\n"
                    f"rating: *{r['rating']}*\n"
                    f"text: {r['text'] or '—'}\n"
                    f"at: `{r['created_at']}`"
                )
                admin_send(chat_id, txt, kb_admin_quick())
                return

        return render_home(chat_id)

    except Exception as e:
        log_exc("on_callback", e)
        safe_send_message(call.message.chat.id, "⚠️ Помилка. Напиши /start")


# ================== TEXT HANDLER ==================
@bot.message_handler(func=lambda m: True, content_types=["text"])
def on_text(message):
    try:
        chat_id = message.chat.id
        ensure_user(chat_id)

        txt = (message.text or "").strip()

        if txt.startswith("/"):
            return

        # ignore admin random text in admin_mode
        if is_admin_message(message) and is_admin_mode():
            return

        st = get_state(chat_id)

        # favorite awaiting mix
        if st and int(st["awaiting_fav_mix"] or 0) == 1:
            key = st["pending_fav_key"]
            mix = (txt[:FAV_MIX_MAX]).strip()
            if key and find_item(key)[1]:
                set_favorite(chat_id, key, mix or None)
            set_state_favorite(chat_id, 0, None)
            try:
                safe_delete(chat_id, message.message_id)
            except Exception:
                pass
            typing(chat_id)
            return render_home(chat_id)

        # feedback awaiting comment
        if st and int(st["awaiting_comment"] or 0) == 1:
            comment = (txt[:COMMENT_MAX]).strip()
            add_feedback(chat_id, st["pending_kind"], int(st["pending_rating"]), st["pending_item_key"], comment or None)
            set_state_feedback(chat_id, 0, None, None, None)
            try:
                safe_delete(chat_id, message.message_id)
            except Exception:
                pass
            typing(chat_id)
            return render_home(chat_id)

        # default
        try:
            safe_delete(chat_id, message.message_id)
        except Exception:
            pass
        typing(chat_id)
        return render_home(chat_id)

    except Exception as e:
        log_exc("on_text", e)
        safe_send_message(message.chat.id, "⚠️ Помилка. Напиши /start")


# ================== RUN ==================
def start_bot():
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception:
        pass

    init_db()
    migrate_db()
    ensure_user(ADMIN_ID)
    load_media_and_overrides()

    print("Bot is running...")
    bot.polling(none_stop=True, interval=0, timeout=30, long_polling_timeout=30)

if __name__ == "__main__":
    start_bot()

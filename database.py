"""SQLite persistence for local CropGuard diagnosis records."""
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_database_url = os.environ.get("DATABASE_URL", "")
_url_path = _database_url[len("sqlite:///"):] if _database_url.startswith("sqlite:///") else ""
_url_path = os.path.join(BASE_DIR, _url_path) if _url_path and not os.path.isabs(_url_path) else _url_path
DB_PATH = os.environ.get("CROPGUARD_DB", _url_path or os.path.join(BASE_DIR, "cropguard.db"))


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            crop TEXT NOT NULL,
            growth_stage TEXT NOT NULL,
            disease TEXT NOT NULL,
            confidence REAL NOT NULL,
            severity TEXT NOT NULL,
            image_path TEXT,
            treatment TEXT NOT NULL DEFAULT '',
            fertilizer TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT ''
        )""")


def save_prediction(*, crop, growth_stage, disease, confidence, severity,
                    image_path=None, treatment=None, fertilizer=None, notes=""):
    init_db()
    with connect() as conn:
        cur = conn.execute("""INSERT INTO predictions
            (date,crop,growth_stage,disease,confidence,severity,image_path,treatment,fertilizer,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now().astimezone().isoformat(timespec="seconds"), crop,
             growth_stage, disease, float(confidence), severity, image_path,
             "\n".join(treatment or []), "\n".join(fertilizer or []), notes))
        return cur.lastrowid


def get_predictions(limit=500):
    init_db()
    with connect() as conn:
        return conn.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()


def update_notes(record_id, notes):
    with connect() as conn:
        conn.execute("UPDATE predictions SET notes=? WHERE id=?", (notes, int(record_id)))


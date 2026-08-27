"""
db.py
-----
All SQLite persistence logic lives here: schema creation and simple
CRUD helpers used by app.py. Using sqlite3 (stdlib) keeps the project
dependency-free for storage and trivially portable (a single .db file).

Schema
------
resumes
    id            INTEGER PRIMARY KEY
    filename      TEXT
    raw_text      TEXT
    uploaded_at   TEXT (ISO timestamp)

analyses
    id                INTEGER PRIMARY KEY
    resume_id         INTEGER  (FK -> resumes.id)
    job_description   TEXT
    ats_score         REAL     -- overall 0-100
    keyword_score     REAL     -- 0-100
    structure_score   REAL     -- 0-100
    matched_keywords  TEXT     -- comma separated
    missing_keywords  TEXT     -- comma separated
    feedback          TEXT     -- AI / rule-based generated feedback
    created_at        TEXT (ISO timestamp)
"""

import sqlite3
import datetime
from contextlib import contextmanager
from typing import List

from config import DB_PATH


@contextmanager
def get_connection():
    """
    Context manager that yields a sqlite3 connection with row access by
    column name, and guarantees the connection is closed afterwards even
    if an exception is raised — prevents locked/leaked DB handles.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Creates tables if they do not already exist. Safe to call on every
    app startup (idempotent), which is exactly how app.py uses it.
    """
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                job_description TEXT,
                ats_score REAL NOT NULL,
                keyword_score REAL NOT NULL,
                structure_score REAL NOT NULL,
                matched_keywords TEXT,
                missing_keywords TEXT,
                feedback TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
            """
        )


def save_resume(filename: str, raw_text: str) -> int:
    """Inserts a resume record and returns its new row id."""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO resumes (filename, raw_text, uploaded_at) VALUES (?, ?, ?)",
            (filename, raw_text, datetime.datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def save_analysis(
    resume_id: int,
    job_description: str,
    ats_score: float,
    keyword_score: float,
    structure_score: float,
    matched_keywords: List[str],
    missing_keywords: List[str],
    feedback: str,
) -> int:
    """Inserts an analysis record tied to a resume and returns its id."""
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO analyses (
                resume_id, job_description, ats_score, keyword_score,
                structure_score, matched_keywords, missing_keywords,
                feedback, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resume_id,
                job_description,
                ats_score,
                keyword_score,
                structure_score,
                ", ".join(matched_keywords),
                ", ".join(missing_keywords),
                feedback,
                datetime.datetime.utcnow().isoformat(),
            ),
        )
        return cur.lastrowid




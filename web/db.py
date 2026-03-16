"""Postgres database for users, chat history, and analytics."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash, check_password_hash


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=False)


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is required (use Supabase Postgres connection string).")
    return url


def get_conn() -> psycopg.Connection:
    return psycopg.connect(_get_database_url(), row_factory=dict_row)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'student',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chats_user_id_created_at
                ON chats (user_id, created_at DESC)
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chats_created_at
                ON chats (created_at DESC)
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS data_deletion_requests (
                    id BIGSERIAL PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    contact_email TEXT NOT NULL,
                    whatsapp_number TEXT,
                    details TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )


def create_user(username, password, role="student"):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username, password_hash, role)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (username, generate_password_hash(password), role),
                )
                row = cur.fetchone()
                return row["id"] if row else None
    except psycopg.IntegrityError:
        return None


def verify_user(username, password):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
    if row and check_password_hash(row["password_hash"], password):
        return row
    return None


def get_user_by_id(user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return row if row else None


def save_chat(user_id, question, answer):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chats (user_id, question, answer) VALUES (%s, %s, %s)",
                (user_id, question, answer),
            )


def get_user_chats(user_id, limit=50):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT question, answer, created_at
                FROM chats
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            return cur.fetchall()


def get_total_users():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM users")
            row = cur.fetchone()
            return int(row["total"] if row else 0)


def get_total_chats():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM chats")
            row = cur.fetchone()
            return int(row["total"] if row else 0)


def get_frequent_questions(limit=10):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT question, COUNT(*) AS count
                FROM chats
                GROUP BY question
                ORDER BY count DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()


def get_recent_chats(limit=20):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.question, c.answer, c.created_at, u.username
                FROM chats c
                JOIN users u ON c.user_id = u.id
                ORDER BY c.created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()


def get_chats_per_day(days=14):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DATE(created_at) AS day, COUNT(*) AS count
                FROM chats
                WHERE created_at >= NOW() - (%s || ' days')::INTERVAL
                GROUP BY day
                ORDER BY day
                """,
                (str(days),),
            )
            rows = cur.fetchall()
    output = []
    for row in rows:
        output.append(
            {
                "day": row["day"].isoformat() if row.get("day") else "",
                "count": int(row.get("count", 0)),
            }
        )
    return output


def get_avg_answer_length():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT AVG(LENGTH(answer)) AS avg_length FROM chats")
            row = cur.fetchone()
            result = row["avg_length"] if row else None
    return round(float(result), 1) if result is not None else 0.0


def create_data_deletion_request(full_name, contact_email, whatsapp_number="", details=""):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO data_deletion_requests (full_name, contact_email, whatsapp_number, details)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (full_name, contact_email, whatsapp_number, details),
            )
            row = cur.fetchone()
            return row["id"] if row else None

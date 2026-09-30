import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "rag_knowledge.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn


def init_db():
    """Initializes tables using the standardized document_chunks schema."""
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    file_path TEXT,
                    file_type TEXT,
                    total_pages INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER,
                    dataset_name TEXT,
                    page_number INTEGER,
                    chunk_index INTEGER,
                    content TEXT,
                    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_name TEXT,
                    session_type TEXT,
                    user_query TEXT,
                    ai_response TEXT,
                    sources TEXT,
                    agent_trace TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
    finally:
        conn.close()


def store_chunk(chunk_id: str, filename: str, page: int, chunk_text: str):
    """Compatibility insert helper for individual chunks."""
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM datasets WHERE name = ?", (filename,))
            row = cursor.fetchone()
            ds_id = row["id"] if row else 1
            cursor.execute(
                """
                INSERT INTO document_chunks (dataset_id, dataset_name, page_number, chunk_index, content)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ds_id, filename, page, 0, chunk_text)
            )
    finally:
        conn.close()


def delete_document_chunks(filename: str) -> int:
    """Deletes chunks and dataset entries matching filename."""
    conn = get_connection()
    purged_count = 0
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE dataset_name = ?", (filename,))
            purged_count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM document_chunks WHERE dataset_name = ?", (filename,))
            cursor.execute("DELETE FROM datasets WHERE name = ?", (filename,))
            cursor.execute("DELETE FROM chat_history WHERE dataset_name = ?", (filename,))
    finally:
        conn.close()
    return purged_count


def save_chat_message(dataset_name: str, session_type: str, user_query: str, ai_response: str, sources: list, agent_trace: list):
    import json
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO chat_history (dataset_name, session_type, user_query, ai_response, sources, agent_trace)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    dataset_name,
                    session_type,
                    user_query,
                    ai_response,
                    json.dumps(sources),
                    json.dumps(agent_trace)
                )
            )
    finally:
        conn.close()


def get_chats_by_dataset(dataset_name: str):
    import json
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM chat_history WHERE dataset_name = ? ORDER BY timestamp DESC LIMIT 20",
            (dataset_name,)
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append({
                "id": r["id"],
                "dataset_name": r["dataset_name"],
                "session_type": r["session_type"],
                "user_query": r["user_query"],
                "ai_response": r["ai_response"],
                "sources": json.loads(r["sources"]) if r["sources"] else [],
                "agent_trace": json.loads(r["agent_trace"]) if r["agent_trace"] else [],
                "timestamp": r["timestamp"]
            })
        return result
    finally:
        conn.close()


def get_all_global_chats():
    return get_chats_by_dataset("Global_Web")


def get_compare_chats():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_history WHERE session_type = 'compare' ORDER BY timestamp DESC LIMIT 20")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


init_db()
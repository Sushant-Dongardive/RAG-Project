import sqlite3
import json
from datetime import datetime
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Datasets / Documents registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                file_path TEXT NOT NULL DEFAULT '',
                file_type TEXT NOT NULL DEFAULT 'pdf',
                total_pages INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Auto-migration in case an old table exists without these columns
        cursor.execute("PRAGMA table_info(datasets)")
        existing_cols = [row["name"] for row in cursor.fetchall()]
        if "file_path" not in existing_cols:
            cursor.execute("ALTER TABLE datasets ADD COLUMN file_path TEXT DEFAULT ''")
        if "file_type" not in existing_cols:
            cursor.execute("ALTER TABLE datasets ADD COLUMN file_type TEXT DEFAULT 'pdf'")
        if "total_pages" not in existing_cols:
            cursor.execute("ALTER TABLE datasets ADD COLUMN total_pages INTEGER DEFAULT 1")
        
        # Chunks table with grounding references
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                dataset_name TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
            )
        """)

        # Chat history per dataset & global mode
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT,
                session_type TEXT DEFAULT 'rag',
                user_query TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                sources TEXT,
                agent_trace TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Multi-Paper comparison conversations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compare_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT NOT NULL,
                doc_a TEXT NOT NULL,
                doc_b TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()

def save_chat_message(dataset_name, session_type, user_query, ai_response, sources=None, agent_trace=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_history (dataset_name, session_type, user_query, ai_response, sources, agent_trace)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            dataset_name,
            session_type,
            user_query,
            ai_response,
            json.dumps(sources or []),
            json.dumps(agent_trace or [])
        ))
        conn.commit()

def get_chats_by_dataset(dataset_name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM chat_history 
            WHERE dataset_name = ? AND session_type = 'rag'
            ORDER BY timestamp DESC
        """, (dataset_name,))
        return [dict(row) for row in cursor.fetchall()]

def get_all_global_chats():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM chat_history 
            WHERE session_type = 'global_ai'
            ORDER BY timestamp DESC
        """, ())
        return [dict(row) for row in cursor.fetchall()]

def get_compare_chats(doc_a=None, doc_b=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if doc_a and doc_b:
            cursor.execute("""
                SELECT * FROM chat_history 
                WHERE session_type = 'compare' AND (dataset_name = ? OR dataset_name = ?)
                ORDER BY timestamp ASC
            """, (f"{doc_a} vs {doc_b}", f"{doc_b} vs {doc_a}"))
        else:
            cursor.execute("""
                SELECT * FROM chat_history 
                WHERE session_type = 'compare'
                ORDER BY timestamp DESC
            """)
        return [dict(row) for row in cursor.fetchall()]
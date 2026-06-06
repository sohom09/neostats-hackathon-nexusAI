"""
memory_manager.py
SQLite-based conversation memory for multi-turn chat sessions.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class MemoryManager:
    def __init__(self, db_path: str = "neostats_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database and create tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT NOT NULL,
                    role        TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    mode        TEXT,
                    sources     TEXT,
                    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session
                ON conversations (session_id, timestamp)
            """)
            conn.commit()

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        mode: Optional[str] = None,
        sources: Optional[List[str]] = None,
    ):
        """Persist a message to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO conversations (session_id, role, content, mode, sources)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, role, content, mode, json.dumps(sources or [])),
            )
            conn.commit()

    def get_history(
        self, session_id: str, limit: int = 12
    ) -> List[Dict]:
        """Retrieve the most recent messages for a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT role, content, mode, sources, timestamp
                FROM conversations
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (session_id, limit),
            )
            rows = cursor.fetchall()

        # Return in chronological order
        return [
            {
                "role": row[0],
                "content": row[1],
                "mode": row[2],
                "sources": json.loads(row[3]) if row[3] else [],
                "timestamp": row[4],
            }
            for row in reversed(rows)
        ]

    def clear_history(self, session_id: str):
        """Delete all messages for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM conversations WHERE session_id = ?", (session_id,)
            )
            conn.commit()

    def get_all_sessions(self) -> List[tuple]:
        """Return summary of all sessions for the history panel."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT session_id,
                       MIN(timestamp) AS created,
                       COUNT(*)       AS message_count
                FROM conversations
                GROUP BY session_id
                ORDER BY created DESC
                LIMIT 20
                """
            )
            return cursor.fetchall()

    def get_session_previews(self) -> List[Dict]:
        """Return sessions with their first user message as a title preview."""
        with sqlite3.connect(self.db_path) as conn:
            # Get distinct sessions ordered by latest activity
            cursor = conn.execute(
                """
                SELECT session_id,
                       MAX(timestamp) AS last_active,
                       COUNT(*)       AS total_msgs
                FROM conversations
                GROUP BY session_id
                ORDER BY last_active DESC
                LIMIT 15
                """
            )
            sessions = cursor.fetchall()

            previews = []
            for session_id, last_active, total_msgs in sessions:
                # Get first user message as title
                c2 = conn.execute(
                    """
                    SELECT content FROM conversations
                    WHERE session_id = ? AND role = 'user'
                    ORDER BY timestamp ASC LIMIT 1
                    """,
                    (session_id,),
                )
                row = c2.fetchone()
                title = row[0][:45] + "…" if row and len(row[0]) > 45 else (row[0] if row else "Empty session")

                # Format timestamp
                try:
                    dt = datetime.strptime(last_active[:19], "%Y-%m-%d %H:%M:%S")
                    ts = dt.strftime("%d %b, %I:%M %p")
                except Exception:
                    ts = last_active[:16] if last_active else ""

                previews.append({
                    "session_id":  session_id,
                    "title":       title,
                    "last_active": ts,
                    "total_msgs":  total_msgs,
                })
            return previews

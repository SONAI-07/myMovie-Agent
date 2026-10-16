import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "bingewatch.db"


def init_db():
    """Initializes the SQLite database and creates the recommendations table if not exists."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id TEXT PRIMARY KEY,
                movie_watched TEXT NOT NULL,
                source TEXT DEFAULT 'web',
                primary_theme TEXT,
                dominant_emotion TEXT,
                cinematic_style TEXT,
                recommendations_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def save_recommendation(
    movie_watched: str,
    pipeline_result: Dict[str, Any],
    source: str = "web"
) -> Dict[str, Any]:
    """Saves a completed movie recommendation run to the SQLite database."""
    init_db()
    rec_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    recs = pipeline_result.get("final_streaming_links") or pipeline_result.get("curated_movies") or []
    recs_json = json.dumps(recs)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recommendations (
                id, movie_watched, source, primary_theme, dominant_emotion, cinematic_style, recommendations_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rec_id,
            movie_watched,
            source,
            pipeline_result.get("primary_theme", ""),
            pipeline_result.get("dominant_emotion", ""),
            pipeline_result.get("cinematic_style", ""),
            recs_json,
            now
        ))
        conn.commit()

    return {
        "id": rec_id,
        "movie_watched": movie_watched,
        "source": source,
        "primary_theme": pipeline_result.get("primary_theme", ""),
        "dominant_emotion": pipeline_result.get("dominant_emotion", ""),
        "cinematic_style": pipeline_result.get("cinematic_style", ""),
        "recommendations": recs,
        "created_at": now
    }


def get_all_recommendations(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves saved recommendations ordered by creation time descending."""
    init_db()
    results = []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, movie_watched, source, primary_theme, dominant_emotion, cinematic_style, recommendations_json, created_at
            FROM recommendations
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()

        for row in rows:
            try:
                recs = json.loads(row["recommendations_json"]) if row["recommendations_json"] else []
            except Exception:
                recs = []

            results.append({
                "id": row["id"],
                "movie_watched": row["movie_watched"],
                "source": row["source"],
                "primary_theme": row["primary_theme"],
                "dominant_emotion": row["dominant_emotion"],
                "cinematic_style": row["cinematic_style"],
                "recommendations": recs,
                "created_at": row["created_at"]
            })

    return results


def delete_recommendation(rec_id: str) -> bool:
    """Deletes a recommendation record by ID."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM recommendations WHERE id = ?", (rec_id,))
        conn.commit()
        return cursor.rowcount > 0

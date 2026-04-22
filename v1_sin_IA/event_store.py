import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "vigilia.db"
DEFAULT_KNOWN_ACCESS_PHRASES = (
    ("abre el porton por favor", "seed_builtin", "canonical_open_request"),
    ("abrir el porton por favor", "seed_builtin", "canonical_open_request"),
    ("abre el porton", "seed_builtin", "canonical_open_request"),
    ("abre la puerta", "seed_builtin", "canonical_open_request"),
    ("dejame pasar", "seed_builtin", "canonical_open_request"),
    ("abril por tom por favor", "seed_observed", "observed_from_access_events"),
)
LEARNED_ACCESS_PHRASE_MIN_SUCCESSES = 2
LEARNED_ACCESS_DECISION_REASON = (
    "voice_requested_open_and_face_match_within_tolerance_and_whitelisted"
)


def normalize_phrase_text(text):
    normalized = unicodedata.normalize("NFKD", (text or "").lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def get_connection(database_path=DATABASE_PATH):
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(database_path)


def ensure_column(connection, table_name, column_name, column_definition):
    existing_columns = {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def initialize_database(database_path=DATABASE_PATH):
    with get_connection(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS access_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                audio_path TEXT,
                transcript TEXT,
                model_response TEXT,
                gate_opened INTEGER NOT NULL DEFAULT 0,
                snapshot_path TEXT,
                error_message TEXT,
                face_match_name TEXT,
                face_match_confidence REAL,
                face_observation_id INTEGER
            )
            """
        )
        ensure_column(connection, "access_events", "face_match_name", "TEXT")
        ensure_column(connection, "access_events", "face_match_confidence", "REAL")
        ensure_column(connection, "access_events", "face_observation_id", "INTEGER")
        ensure_column(connection, "access_events", "decision_source", "TEXT")
        ensure_column(connection, "access_events", "decision_reason", "TEXT")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS authorized_people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                reference_image_path TEXT,
                face_embedding_json TEXT,
                notes TEXT
            )
            """
        )
        ensure_column(connection, "authorized_people", "access_enabled", "INTEGER NOT NULL DEFAULT 1")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS face_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                image_path TEXT,
                matched_person_id INTEGER,
                confidence REAL,
                face_embedding_json TEXT,
                notes TEXT,
                FOREIGN KEY (matched_person_id) REFERENCES authorized_people(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS known_access_phrases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                phrase_text TEXT NOT NULL,
                normalized_phrase TEXT NOT NULL UNIQUE,
                source TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                notes TEXT
            )
            """
        )
        seed_known_access_phrases(connection)
        connection.commit()


def seed_known_access_phrases(connection):
    for phrase_text, source, notes in DEFAULT_KNOWN_ACCESS_PHRASES:
        connection.execute(
            """
            INSERT OR IGNORE INTO known_access_phrases (
                created_at,
                phrase_text,
                normalized_phrase,
                source,
                enabled,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                phrase_text,
                normalize_phrase_text(phrase_text),
                source,
                1,
                notes,
            ),
        )


def insert_access_event(
    created_at,
    audio_path,
    transcript,
    model_response,
    gate_opened,
    snapshot_path=None,
    error_message=None,
    face_match_name=None,
    face_match_confidence=None,
    face_observation_id=None,
    decision_source=None,
    decision_reason=None,
    database_path=DATABASE_PATH,
):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO access_events (
                created_at,
                audio_path,
                transcript,
                model_response,
                gate_opened,
                snapshot_path,
                error_message,
                face_match_name,
                face_match_confidence,
                face_observation_id,
                decision_source,
                decision_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                audio_path,
                transcript,
                model_response,
                int(bool(gate_opened)),
                snapshot_path,
                error_message,
                face_match_name,
                face_match_confidence,
                face_observation_id,
                decision_source,
                decision_reason,
            ),
        )
        connection.commit()
        return cursor.lastrowid


def get_recent_access_events(limit=10, database_path=DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT
                id,
                created_at,
                audio_path,
                transcript,
                model_response,
                gate_opened,
                snapshot_path,
                error_message,
                face_match_name,
                face_match_confidence,
                face_observation_id,
                decision_source,
                decision_reason
            FROM access_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]


def insert_authorized_person(
    name,
    reference_image_path=None,
    face_embedding_json=None,
    notes=None,
    access_enabled=True,
    created_at=None,
    database_path=DATABASE_PATH,
):
    initialize_database(database_path)
    created_at = created_at or datetime.now().isoformat(timespec="seconds")

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO authorized_people (
                created_at,
                name,
                reference_image_path,
                face_embedding_json,
                notes,
                access_enabled
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                name,
                reference_image_path,
                face_embedding_json,
                notes,
                int(bool(access_enabled)),
            ),
        )
        connection.commit()
        return cursor.lastrowid


def get_authorized_people(database_path=DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT
                id,
                created_at,
                name,
                reference_image_path,
                face_embedding_json,
                notes,
                access_enabled
            FROM authorized_people
            ORDER BY id DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def set_authorized_person_access(
    person_id,
    access_enabled,
    database_path=DATABASE_PATH,
):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE authorized_people
            SET access_enabled = ?
            WHERE id = ?
            """,
            (
                int(bool(access_enabled)),
                person_id,
            ),
        )
        connection.commit()
        return cursor.rowcount


def update_authorized_person_reference_image(
    person_id,
    reference_image_path,
    database_path=DATABASE_PATH,
):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE authorized_people
            SET reference_image_path = ?
            WHERE id = ?
            """,
            (
                reference_image_path,
                person_id,
            ),
        )
        connection.commit()
        return cursor.rowcount


def delete_authorized_person(
    person_id,
    database_path=DATABASE_PATH,
):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            DELETE FROM authorized_people
            WHERE id = ?
            """,
            (person_id,),
        )
        connection.commit()
        return cursor.rowcount


def insert_face_observation(
    image_path=None,
    matched_person_id=None,
    confidence=None,
    face_embedding_json=None,
    notes=None,
    created_at=None,
    database_path=DATABASE_PATH,
):
    initialize_database(database_path)
    created_at = created_at or datetime.now().isoformat(timespec="seconds")

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO face_observations (
                created_at,
                image_path,
                matched_person_id,
                confidence,
                face_embedding_json,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                image_path,
                matched_person_id,
                confidence,
                face_embedding_json,
                notes,
            ),
        )
        connection.commit()
        return cursor.lastrowid


def get_recent_face_observations(limit=10, database_path=DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT
                o.id,
                o.created_at,
                o.image_path,
                o.matched_person_id,
                p.name AS matched_person_name,
                o.confidence,
                o.face_embedding_json,
                o.notes
            FROM face_observations o
            LEFT JOIN authorized_people p ON p.id = o.matched_person_id
            ORDER BY o.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_enabled_access_phrases(database_path=DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            SELECT normalized_phrase
            FROM known_access_phrases
            WHERE enabled = 1
            ORDER BY id DESC
            """
        )
        known_phrases = [row[0] for row in cursor.fetchall()]

        learned_cursor = connection.execute(
            """
            SELECT transcript, COUNT(*) AS total
            FROM access_events
            WHERE gate_opened = 1
              AND decision_reason = ?
              AND transcript IS NOT NULL
              AND TRIM(transcript) != ''
            GROUP BY transcript
            HAVING COUNT(*) >= ?
            ORDER BY total DESC
            """,
            (
                LEARNED_ACCESS_DECISION_REASON,
                LEARNED_ACCESS_PHRASE_MIN_SUCCESSES,
            ),
        )
        learned_phrases = [
            normalize_phrase_text(row[0])
            for row in learned_cursor.fetchall()
            if normalize_phrase_text(row[0])
        ]

        # Keep order stable while de-duplicating known and learned phrases.
        deduped_phrases = []
        for phrase in known_phrases + learned_phrases:
            if phrase not in deduped_phrases:
                deduped_phrases.append(phrase)
        return deduped_phrases

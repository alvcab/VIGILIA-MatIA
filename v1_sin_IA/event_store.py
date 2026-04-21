import sqlite3
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "vigilia.db"


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
        connection.commit()


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

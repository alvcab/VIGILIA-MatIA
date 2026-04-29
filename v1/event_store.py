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
        ensure_column(connection, "access_events", "claimed_resident_name", "TEXT")
        ensure_column(connection, "access_events", "claimed_unit", "TEXT")
        ensure_column(connection, "access_events", "resolved_resident_id", "INTEGER")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS residents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                full_name TEXT NOT NULL,
                preferred_name TEXT,
                apartment_unit TEXT,
                building TEXT,
                phone_primary TEXT,
                phone_secondary TEXT,
                access_enabled INTEGER NOT NULL DEFAULT 1,
                notes TEXT
            )
            """
        )
        ensure_column(connection, "residents", "ownership_share", "REAL")
        ensure_column(connection, "residents", "resident_role", "TEXT")
        ensure_column(connection, "residents", "validation_status", "TEXT")
        ensure_column(connection, "residents", "is_account_manager", "INTEGER")
        ensure_column(connection, "residents", "email_primary", "TEXT")
        ensure_column(connection, "residents", "tax_id", "TEXT")
        ensure_column(connection, "residents", "system_enrolled", "INTEGER")
        ensure_column(connection, "residents", "last_system_access", "TEXT")
        ensure_column(connection, "residents", "source", "TEXT")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS resident_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                resident_id INTEGER NOT NULL,
                alias_text TEXT NOT NULL,
                normalized_alias TEXT NOT NULL,
                alias_type TEXT NOT NULL DEFAULT 'name',
                notes TEXT,
                UNIQUE(resident_id, normalized_alias, alias_type),
                FOREIGN KEY (resident_id) REFERENCES residents(id)
            )
            """
        )
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
        ensure_column(connection, "authorized_people", "resident_id", "INTEGER")
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
    claimed_resident_name=None,
    claimed_unit=None,
    resolved_resident_id=None,
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
                decision_reason,
                claimed_resident_name,
                claimed_unit,
                resolved_resident_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                claimed_resident_name,
                claimed_unit,
                resolved_resident_id,
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
                decision_reason,
                claimed_resident_name,
                claimed_unit,
                resolved_resident_id
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
    resident_id=None,
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
                access_enabled,
                resident_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                name,
                reference_image_path,
                face_embedding_json,
                notes,
                int(bool(access_enabled)),
                resident_id,
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
                access_enabled,
                resident_id
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


def update_authorized_person_resident_id(
    person_id,
    resident_id,
    database_path=DATABASE_PATH,
):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE authorized_people
            SET resident_id = ?
            WHERE id = ?
            """,
            (
                resident_id,
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


def insert_resident(
    full_name,
    preferred_name=None,
    apartment_unit=None,
    building=None,
    phone_primary=None,
    phone_secondary=None,
    ownership_share=None,
    resident_role=None,
    validation_status=None,
    is_account_manager=None,
    email_primary=None,
    tax_id=None,
    system_enrolled=None,
    last_system_access=None,
    source=None,
    access_enabled=True,
    notes=None,
    created_at=None,
    database_path=DATABASE_PATH,
):
    initialize_database(database_path)
    created_at = created_at or datetime.now().isoformat(timespec="seconds")
    updated_at = created_at

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO residents (
                created_at,
                updated_at,
                full_name,
                preferred_name,
                apartment_unit,
                building,
                phone_primary,
                phone_secondary,
                ownership_share,
                resident_role,
                validation_status,
                is_account_manager,
                email_primary,
                tax_id,
                system_enrolled,
                last_system_access,
                source,
                access_enabled,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                updated_at,
                full_name,
                preferred_name,
                apartment_unit,
                building,
                phone_primary,
                phone_secondary,
                ownership_share,
                resident_role,
                validation_status,
                None if is_account_manager is None else int(bool(is_account_manager)),
                email_primary,
                tax_id,
                None if system_enrolled is None else int(bool(system_enrolled)),
                last_system_access,
                source,
                int(bool(access_enabled)),
                notes,
            ),
        )
        connection.commit()
        return cursor.lastrowid


def find_matching_resident(
    full_name,
    apartment_unit=None,
    email_primary=None,
    phone_primary=None,
    database_path=DATABASE_PATH,
):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        connection.row_factory = sqlite3.Row
        candidates = connection.execute(
            """
            SELECT *
            FROM residents
            WHERE full_name = ?
              AND COALESCE(apartment_unit, '') = COALESCE(?, '')
            ORDER BY id DESC
            """,
            (
                full_name,
                apartment_unit,
            ),
        ).fetchall()

        if not candidates:
            return None

        if email_primary or phone_primary:
            for candidate in candidates:
                if email_primary and candidate["email_primary"] == email_primary:
                    return dict(candidate)
                if phone_primary and candidate["phone_primary"] == phone_primary:
                    return dict(candidate)

        return dict(candidates[0])


def upsert_resident(
    full_name,
    preferred_name=None,
    apartment_unit=None,
    building=None,
    phone_primary=None,
    phone_secondary=None,
    ownership_share=None,
    resident_role=None,
    validation_status=None,
    is_account_manager=None,
    email_primary=None,
    tax_id=None,
    system_enrolled=None,
    last_system_access=None,
    source=None,
    access_enabled=True,
    notes=None,
    database_path=DATABASE_PATH,
):
    existing = find_matching_resident(
        full_name=full_name,
        apartment_unit=apartment_unit,
        email_primary=email_primary,
        phone_primary=phone_primary,
        database_path=database_path,
    )
    if existing:
        updates = {
            "preferred_name": preferred_name,
            "building": building,
            "phone_primary": phone_primary,
            "phone_secondary": phone_secondary,
            "ownership_share": ownership_share,
            "resident_role": resident_role,
            "validation_status": validation_status,
            "is_account_manager": (
                None if is_account_manager is None else int(bool(is_account_manager))
            ),
            "email_primary": email_primary,
            "tax_id": tax_id,
            "system_enrolled": (
                None if system_enrolled is None else int(bool(system_enrolled))
            ),
            "last_system_access": last_system_access,
            "source": source,
            "access_enabled": int(bool(access_enabled)),
            "notes": notes,
        }
        changed_columns = []
        changed_values = []
        for column_name, candidate_value in updates.items():
            if candidate_value in (None, ""):
                continue
            existing_value = existing.get(column_name)
            if str(existing_value or "") == str(candidate_value):
                continue
            changed_columns.append(f"{column_name} = ?")
            changed_values.append(candidate_value)

        if changed_columns:
            changed_columns.append("updated_at = ?")
            changed_values.append(datetime.now().isoformat(timespec="seconds"))
            changed_values.append(existing["id"])
            initialize_database(database_path)
            with get_connection(database_path) as connection:
                connection.execute(
                    f"""
                    UPDATE residents
                    SET {", ".join(changed_columns)}
                    WHERE id = ?
                    """,
                    tuple(changed_values),
                )
                connection.commit()
        return existing["id"], False

    resident_id = insert_resident(
        full_name=full_name,
        preferred_name=preferred_name,
        apartment_unit=apartment_unit,
        building=building,
        phone_primary=phone_primary,
        phone_secondary=phone_secondary,
        ownership_share=ownership_share,
        resident_role=resident_role,
        validation_status=validation_status,
        is_account_manager=is_account_manager,
        email_primary=email_primary,
        tax_id=tax_id,
        system_enrolled=system_enrolled,
        last_system_access=last_system_access,
        source=source,
        access_enabled=access_enabled,
        notes=notes,
        database_path=database_path,
    )
    return resident_id, True


def get_residents(database_path=DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT
                id,
                created_at,
                updated_at,
                full_name,
                preferred_name,
                apartment_unit,
                building,
                phone_primary,
                phone_secondary,
                ownership_share,
                resident_role,
                validation_status,
                is_account_manager,
                email_primary,
                tax_id,
                system_enrolled,
                last_system_access,
                source,
                access_enabled,
                notes
            FROM residents
            ORDER BY id DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def insert_resident_alias(
    resident_id,
    alias_text,
    alias_type="name",
    notes=None,
    created_at=None,
    database_path=DATABASE_PATH,
):
    initialize_database(database_path)
    created_at = created_at or datetime.now().isoformat(timespec="seconds")
    normalized_alias = normalize_phrase_text(alias_text)

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO resident_aliases (
                created_at,
                resident_id,
                alias_text,
                normalized_alias,
                alias_type,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                resident_id,
                alias_text,
                normalized_alias,
                alias_type,
                notes,
            ),
        )
        connection.commit()
        return cursor.lastrowid


def get_resident_aliases(database_path=DATABASE_PATH):
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT
                a.id,
                a.created_at,
                a.resident_id,
                r.full_name AS resident_name,
                a.alias_text,
                a.normalized_alias,
                a.alias_type,
                a.notes
            FROM resident_aliases a
            JOIN residents r ON r.id = a.resident_id
            ORDER BY a.id DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]

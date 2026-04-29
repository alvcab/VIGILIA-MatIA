import sys

try:
    from v1.event_store import (
        delete_authorized_person,
        get_authorized_people,
        get_recent_face_observations,
        insert_authorized_person,
        insert_face_observation,
        set_authorized_person_access,
        update_authorized_person_resident_id,
        update_authorized_person_reference_image,
    )
except ModuleNotFoundError:
    from event_store import (
        delete_authorized_person,
        get_authorized_people,
        get_recent_face_observations,
        insert_authorized_person,
        insert_face_observation,
        set_authorized_person_access,
        update_authorized_person_resident_id,
        update_authorized_person_reference_image,
    )


def print_usage():
    print("Uso:")
    print("  python3 v1/face_registry.py add-person <nombre> [reference_image_path] [allow|deny] [resident_id]")
    print("  python3 v1/face_registry.py list-people")
    print("  python3 v1/face_registry.py set-access <person_id> <allow|deny>")
    print("  python3 v1/face_registry.py set-resident <person_id> <resident_id>")
    print("  python3 v1/face_registry.py update-reference-image <person_id> <reference_image_path>")
    print("  python3 v1/face_registry.py remove-person <person_id>")
    print("  python3 v1/face_registry.py add-observation [image_path] [notes]")
    print("  python3 v1/face_registry.py list-observations [limite]")


def add_person(args):
    if len(args) < 1:
        print_usage()
        sys.exit(1)

    name = args[0]
    reference_image_path = args[1] if len(args) > 1 else None
    access_enabled = True
    resident_id = None

    if len(args) > 2:
        access_enabled = args[2].lower() != "deny"
    if len(args) > 3:
        resident_id = int(args[3])

    person_id = insert_authorized_person(
        name=name,
        reference_image_path=reference_image_path,
        notes="manual_registry_entry",
        access_enabled=access_enabled,
        resident_id=resident_id,
    )
    print(f"Persona autorizada guardada con id={person_id}")


def list_people():
    people = get_authorized_people()
    if not people:
        print("No hay personas autorizadas registradas todavia.")
        return

    for person in people:
        print(f"id: {person['id']}")
        print(f"name: {person['name']}")
        print(f"created_at: {person['created_at']}")
        print(f"resident_id: {person.get('resident_id') or '-'}")
        print(f"reference_image_path: {person['reference_image_path'] or '-'}")
        print(f"access_enabled: {bool(person.get('access_enabled', 1))}")
        print(f"notes: {person['notes'] or '-'}")
        print("-" * 40)


def add_observation(args):
    image_path = args[0] if len(args) > 0 else None
    notes = args[1] if len(args) > 1 else "manual_face_observation"
    observation_id = insert_face_observation(
        image_path=image_path,
        notes=notes,
    )
    print(f"Observacion facial guardada con id={observation_id}")


def set_access(args):
    if len(args) != 2:
        print_usage()
        sys.exit(1)

    try:
        person_id = int(args[0])
    except ValueError:
        print("person_id debe ser numerico.")
        sys.exit(1)

    mode = args[1].lower()
    if mode not in {"allow", "deny"}:
        print("El modo debe ser allow o deny.")
        sys.exit(1)

    updated_rows = set_authorized_person_access(
        person_id=person_id,
        access_enabled=(mode == "allow"),
    )

    if updated_rows == 0:
        print(f"No existe una persona con id={person_id}.")
        sys.exit(1)

    print(
        f"Persona id={person_id} actualizada con access_enabled={mode == 'allow'}"
    )


def update_reference_image(args):
    if len(args) != 2:
        print_usage()
        sys.exit(1)

    try:
        person_id = int(args[0])
    except ValueError:
        print("person_id debe ser numerico.")
        sys.exit(1)

    reference_image_path = args[1]
    updated_rows = update_authorized_person_reference_image(
        person_id=person_id,
        reference_image_path=reference_image_path,
    )

    if updated_rows == 0:
        print(f"No existe una persona con id={person_id}.")
        sys.exit(1)

    print(
        f"Persona id={person_id} actualizada con reference_image_path={reference_image_path}"
    )


def set_resident(args):
    if len(args) != 2:
        print_usage()
        sys.exit(1)

    try:
        person_id = int(args[0])
        resident_id = int(args[1])
    except ValueError:
        print("person_id y resident_id deben ser numericos.")
        sys.exit(1)

    updated_rows = update_authorized_person_resident_id(
        person_id=person_id,
        resident_id=resident_id,
    )

    if updated_rows == 0:
        print(f"No existe una persona con id={person_id}.")
        sys.exit(1)

    print(f"Persona id={person_id} vinculada a resident_id={resident_id}.")


def remove_person(args):
    if len(args) != 1:
        print_usage()
        sys.exit(1)

    try:
        person_id = int(args[0])
    except ValueError:
        print("person_id debe ser numerico.")
        sys.exit(1)

    deleted_rows = delete_authorized_person(person_id=person_id)

    if deleted_rows == 0:
        print(f"No existe una persona con id={person_id}.")
        sys.exit(1)

    print(f"Persona id={person_id} eliminada del registro.")


def list_observations(args):
    limit = 10
    if args:
        limit = int(args[0])

    observations = get_recent_face_observations(limit=limit)
    if not observations:
        print("No hay observaciones faciales registradas todavia.")
        return

    for observation in observations:
        print(f"id: {observation['id']}")
        print(f"created_at: {observation['created_at']}")
        print(f"image_path: {observation['image_path'] or '-'}")
        print(f"matched_person_id: {observation['matched_person_id'] or '-'}")
        print(f"matched_person_name: {observation['matched_person_name'] or '-'}")
        print(f"confidence: {observation['confidence'] if observation['confidence'] is not None else '-'}")
        print(f"notes: {observation['notes'] or '-'}")
        print("-" * 40)


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "add-person":
        add_person(args)
        return

    if command == "list-people":
        list_people()
        return

    if command == "add-observation":
        add_observation(args)
        return

    if command == "set-access":
        set_access(args)
        return

    if command == "update-reference-image":
        update_reference_image(args)
        return

    if command == "set-resident":
        set_resident(args)
        return

    if command == "remove-person":
        remove_person(args)
        return

    if command == "list-observations":
        list_observations(args)
        return

    print_usage()
    sys.exit(1)


if __name__ == "__main__":
    main()

import sys

try:
    from v1_sin_IA.event_store import (
        get_authorized_people,
        get_recent_face_observations,
        insert_authorized_person,
        insert_face_observation,
    )
except ModuleNotFoundError:
    from event_store import (
        get_authorized_people,
        get_recent_face_observations,
        insert_authorized_person,
        insert_face_observation,
    )


def print_usage():
    print("Uso:")
    print("  python3 v1_sin_IA/face_registry.py add-person <nombre> [reference_image_path]")
    print("  python3 v1_sin_IA/face_registry.py list-people")
    print("  python3 v1_sin_IA/face_registry.py add-observation [image_path] [notes]")
    print("  python3 v1_sin_IA/face_registry.py list-observations [limite]")


def add_person(args):
    if len(args) < 1:
        print_usage()
        sys.exit(1)

    name = args[0]
    reference_image_path = args[1] if len(args) > 1 else None
    person_id = insert_authorized_person(
        name=name,
        reference_image_path=reference_image_path,
        notes="manual_registry_entry",
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
        print(f"reference_image_path: {person['reference_image_path'] or '-'}")
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

    if command == "list-observations":
        list_observations(args)
        return

    print_usage()
    sys.exit(1)


if __name__ == "__main__":
    main()

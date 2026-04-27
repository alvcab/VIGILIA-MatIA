import sys

try:
    from v1_sin_IA.event_store import (
        get_resident_aliases,
        get_residents,
        insert_resident,
        insert_resident_alias,
    )
except ModuleNotFoundError:
    from event_store import (
        get_resident_aliases,
        get_residents,
        insert_resident,
        insert_resident_alias,
    )


def print_usage():
    print("Uso:")
    print("  python3 v1_sin_IA/resident_registry.py add-resident <full_name> [preferred_name] [unit] [building] [phone]")
    print("  python3 v1_sin_IA/resident_registry.py list-residents")
    print("  python3 v1_sin_IA/resident_registry.py add-alias <resident_id> <alias_text> [alias_type]")
    print("  python3 v1_sin_IA/resident_registry.py list-aliases")


def add_resident(args):
    if len(args) < 1:
        print_usage()
        sys.exit(1)

    resident_id = insert_resident(
        full_name=args[0],
        preferred_name=args[1] if len(args) > 1 else None,
        apartment_unit=args[2] if len(args) > 2 else None,
        building=args[3] if len(args) > 3 else None,
        phone_primary=args[4] if len(args) > 4 else None,
        notes="manual_resident_entry",
    )
    print(f"Residente guardado con id={resident_id}")


def list_residents():
    residents = get_residents()
    if not residents:
        print("No hay residentes registrados todavia.")
        return

    for resident in residents:
        print(f"id: {resident['id']}")
        print(f"full_name: {resident['full_name']}")
        print(f"preferred_name: {resident['preferred_name'] or '-'}")
        print(f"apartment_unit: {resident['apartment_unit'] or '-'}")
        print(f"building: {resident['building'] or '-'}")
        print(f"resident_role: {resident.get('resident_role') or '-'}")
        print(f"validation_status: {resident.get('validation_status') or '-'}")
        print(f"ownership_share: {resident.get('ownership_share') or '-'}")
        print(f"email_primary: {resident.get('email_primary') or '-'}")
        print(f"phone_primary: {resident['phone_primary'] or '-'}")
        print(f"tax_id: {resident.get('tax_id') or '-'}")
        print(f"system_enrolled: {resident.get('system_enrolled')}")
        print(f"access_enabled: {bool(resident.get('access_enabled', 1))}")
        print(f"source: {resident.get('source') or '-'}")
        print(f"notes: {resident['notes'] or '-'}")
        print("-" * 40)


def add_alias(args):
    if len(args) < 2:
        print_usage()
        sys.exit(1)

    resident_id = int(args[0])
    alias_text = args[1]
    alias_type = args[2] if len(args) > 2 else "name"
    alias_id = insert_resident_alias(
        resident_id=resident_id,
        alias_text=alias_text,
        alias_type=alias_type,
        notes="manual_resident_alias",
    )
    print(f"Alias guardado con id={alias_id}")


def list_aliases():
    aliases = get_resident_aliases()
    if not aliases:
        print("No hay aliases registrados todavia.")
        return

    for alias in aliases:
        print(f"id: {alias['id']}")
        print(f"resident_id: {alias['resident_id']}")
        print(f"resident_name: {alias['resident_name']}")
        print(f"alias_text: {alias['alias_text']}")
        print(f"normalized_alias: {alias['normalized_alias']}")
        print(f"alias_type: {alias['alias_type']}")
        print(f"notes: {alias['notes'] or '-'}")
        print("-" * 40)


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "add-resident":
        add_resident(args)
        return

    if command == "list-residents":
        list_residents()
        return

    if command == "add-alias":
        add_alias(args)
        return

    if command == "list-aliases":
        list_aliases()
        return

    print_usage()
    sys.exit(1)


if __name__ == "__main__":
    main()

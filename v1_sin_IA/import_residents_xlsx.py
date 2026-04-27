import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

try:
    from v1_sin_IA.event_store import insert_resident_alias, upsert_resident
except ModuleNotFoundError:
    from event_store import insert_resident_alias, upsert_resident


WORKBOOK_SHEET_NAME = "Listado de Copropietarios"
BUILDING_NAME = "Edificio Medanos Park"
SOURCE_NAME = "xlsx_residentes_medanos_park"
XML_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}
EXPECTED_HEADERS = (
    "Unidad",
    "Prorrateo",
    "Nombre y apellido",
    "Rol",
    "Estado de rol",
    "Encargado",
    "Correo",
    "Telefono",
    "RUT",
    "Ingreso al sistema",
    "Ultimo ingreso",
)


def print_usage():
    print("Uso:")
    print(
        "  python3 v1_sin_IA/import_residents_xlsx.py "
        "\"/ruta/al/archivo.xlsx\""
    )


def normalize_text(value):
    if value is None:
        return None
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    return value or None


def slugify_text(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    return normalized or "resident"


def normalize_header(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def parse_bool(value):
    normalized = normalize_text(value)
    if not normalized:
        return None
    lowered = normalized.lower()
    if lowered in {"si", "sí", "yes", "true", "1"}:
        return True
    if lowered in {"no", "false", "0"}:
        return False
    return None


def parse_float(value):
    normalized = normalize_text(value)
    if not normalized:
        return None
    try:
        return float(normalized.replace(",", "."))
    except ValueError:
        return None


def preferred_name_from_full_name(full_name):
    parts = (full_name or "").split()
    return parts[0] if parts else None


def make_aliases(full_name, apartment_unit):
    aliases = []
    if full_name:
        aliases.append((full_name, "name"))
        aliases.append((full_name.lower(), "name_variant"))
    if apartment_unit:
        aliases.append((apartment_unit, "unit"))
        aliases.append((f"depto {apartment_unit}", "unit"))
        aliases.append((f"departamento {apartment_unit}", "unit"))
        aliases.append((f"unidad {apartment_unit}", "unit"))

    deduped = []
    seen = set()
    for alias_text, alias_type in aliases:
        key = (normalize_text(alias_text), alias_type)
        if not key[0] or key in seen:
            continue
        seen.add(key)
        deduped.append((key[0], alias_type))
    return deduped


def excel_column_index(cell_reference):
    letters = []
    for char in cell_reference:
        if char.isalpha():
            letters.append(char)
        else:
            break
    index = 0
    for char in letters:
        index = index * 26 + (ord(char.upper()) - 64)
    return index


def extract_cell_value(cell):
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        inline = cell.find("a:is", XML_NS)
        return "".join(inline.itertext()).strip() if inline is not None else ""
    value_node = cell.find("a:v", XML_NS)
    return (value_node.text or "").strip() if value_node is not None else ""


def workbook_sheet_path(workbook_path, sheet_name):
    with ZipFile(workbook_path) as workbook_zip:
        workbook_root = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
        rels_root = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels_root.findall("pr:Relationship", XML_NS)
        }
        for sheet in workbook_root.find("a:sheets", XML_NS):
            if sheet.attrib.get("name") != sheet_name:
                continue
            rel_id = sheet.attrib[
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            ]
            return f"xl/{rel_map[rel_id]}"
    raise ValueError(f"No se encontro la hoja {sheet_name!r} en el workbook.")


def load_rows_from_sheet(workbook_path, sheet_name):
    sheet_path = workbook_sheet_path(workbook_path, sheet_name)
    with ZipFile(workbook_path) as workbook_zip:
        sheet_root = ET.fromstring(workbook_zip.read(sheet_path))

    rows = []
    for row in sheet_root.find("a:sheetData", XML_NS).findall("a:row", XML_NS):
        values_by_index = {}
        for cell in row.findall("a:c", XML_NS):
            values_by_index[excel_column_index(cell.attrib["r"])] = extract_cell_value(
                cell
            )
        if not values_by_index:
            continue
        row_values = [values_by_index.get(index, "") for index in range(1, 13)]
        rows.append(row_values)
    return rows


def extract_records(workbook_path):
    rows = load_rows_from_sheet(workbook_path, WORKBOOK_SHEET_NAME)
    header_index = None
    for index, row_values in enumerate(rows):
        normalized_headers = tuple(normalize_header(value) for value in row_values[1:12])
        if normalized_headers == EXPECTED_HEADERS:
            header_index = index
            break

    if header_index is None:
        raise ValueError("No pude encontrar la fila de encabezados esperada en el Excel.")

    records = []
    for row_values in rows[header_index + 1 :]:
        data_values = row_values[1:12]
        if not any(normalize_text(value) for value in data_values):
            continue

        unit = normalize_text(data_values[0])
        full_name = normalize_text(data_values[2])
        if not full_name:
            continue

        records.append(
            {
                "apartment_unit": unit,
                "ownership_share": parse_float(data_values[1]),
                "full_name": full_name,
                "resident_role": normalize_text(data_values[3]),
                "validation_status": normalize_text(data_values[4]),
                "is_account_manager": parse_bool(data_values[5]),
                "email_primary": normalize_text(data_values[6]),
                "phone_primary": normalize_text(data_values[7]),
                "tax_id": normalize_text(data_values[8]),
                "system_enrolled": parse_bool(data_values[9]),
                "last_system_access": normalize_text(data_values[10]),
            }
        )
    return records


def import_workbook(workbook_path):
    records = extract_records(workbook_path)
    created_count = 0
    updated_count = 0
    alias_inserted_count = 0
    alias_skipped_count = 0

    for record in records:
        resident_id, created = upsert_resident(
            full_name=record["full_name"],
            preferred_name=preferred_name_from_full_name(record["full_name"]),
            apartment_unit=record["apartment_unit"],
            building=BUILDING_NAME,
            phone_primary=record["phone_primary"],
            ownership_share=record["ownership_share"],
            resident_role=record["resident_role"],
            validation_status=record["validation_status"],
            is_account_manager=record["is_account_manager"],
            email_primary=record["email_primary"],
            tax_id=record["tax_id"],
            system_enrolled=record["system_enrolled"],
            last_system_access=record["last_system_access"],
            source=SOURCE_NAME,
            notes=f"imported_from_{slugify_text(Path(workbook_path).stem)}",
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

        for alias_text, alias_type in make_aliases(
            record["full_name"], record["apartment_unit"]
        ):
            alias_id = insert_resident_alias(
                resident_id=resident_id,
                alias_text=alias_text,
                alias_type=alias_type,
                notes=SOURCE_NAME,
            )
            if alias_id:
                alias_inserted_count += 1
            else:
                alias_skipped_count += 1

    return {
        "records": len(records),
        "created": created_count,
        "updated_or_reused": updated_count,
        "aliases_created": alias_inserted_count,
        "aliases_skipped": alias_skipped_count,
    }


def main():
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    workbook_path = Path(sys.argv[1]).expanduser()
    if not workbook_path.exists():
        print(f"No se encontro el archivo: {workbook_path}")
        sys.exit(1)

    summary = import_workbook(workbook_path)
    print(f"Archivo importado: {workbook_path}")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

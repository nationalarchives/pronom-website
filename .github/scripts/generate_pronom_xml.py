import json
import os
import sys
import xml.etree.ElementTree as Et
from pathlib import Path

NS = "http://pronom.nationalarchives.gov.uk"
Et.register_namespace("", NS)


def q(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def text_or_space(value) -> str:
    if value is None:
        return " "
    string_value = str(value)
    return string_value if string_value else " "


def add_text_element(parent: Et.Element, tag: str, value) -> Et.Element:
    element = Et.SubElement(parent, q(tag))
    element.text = text_or_space(value)
    return element


def get_org_and_name(name: str):
    if " / " in name:
        return tuple(name.split(" / "))
    return (
        None,
        name,
    )


def create_concatenated_actor(actor_ids: list, actors_by_id: dict):
    names = []
    orgs = []
    compound_names = []
    for actor_id in actor_ids:
        actor_name = actors_by_id[actor_id]["name"]
        name, org = get_org_and_name(actor_name)
        names.append(name)
        orgs.append(org)
        compound_name = f"{name} / {org}" if name else org
        compound_names.append(compound_name)
    return (
        ",".join(str(i) for i in actor_ids),
        ",".join(" " if not n else n for n in names),
        ",".join(orgs),
        ",".join(compound_names),
    )


def build_file_format_element(
    format_json: dict, actors_by_id: dict, signatures_by_id: dict
) -> Et.Element:
    file_format = Et.Element(q("FileFormat"))

    add_text_element(file_format, "FormatID", format_json.get("fileFormatID"))
    add_text_element(file_format, "FormatName", format_json.get("formatName"))
    add_text_element(file_format, "FormatVersion", format_json.get("version"))
    add_text_element(file_format, "FormatAliases", format_json.get("formatAliases"))
    add_text_element(file_format, "FormatFamilies", format_json.get("formatFamilies"))
    add_text_element(file_format, "FormatTypes", format_json.get("formatTypes"))
    add_text_element(
        file_format, "FormatDisclosure", format_json.get("formatDisclosure")
    )
    add_text_element(
        file_format, "FormatDescription", format_json.get("formatDescription")
    )
    add_text_element(
        file_format, "BinaryFileFormat", format_json.get("binaryFileFormat")
    )
    add_text_element(file_format, "ReleaseDate", format_json.get("releaseDate"))
    for submitted_by in format_json.get("submittedBy", [None]):
        add_text_element(file_format, "ProvenanceSourceID", submitted_by)
        add_text_element(
            file_format, "ProvenanceName", actors_by_id[submitted_by].get("name")
        )

    add_text_element(
        file_format, "ProvenanceSourceDate", format_json.get("formatSourceDate")
    )
    add_text_element(
        file_format, "ProvenanceDescription", format_json.get("formatProvenance")
    )
    add_text_element(file_format, "LastUpdatedDate", format_json.get("lastUpdatedDate"))

    for identifier in format_json.get("identifiers", []):
        identifier_element = Et.SubElement(file_format, q("FileFormatIdentifier"))
        add_text_element(
            identifier_element, "Identifier", identifier.get("identifierText")
        )
        add_text_element(
            identifier_element, "IdentifierType", identifier.get("identifierType")
        )

    if format_json.get("developedBy"):
        developer_id, developer_name, developer_org, developer_compound_name = (
            create_concatenated_actor(format_json["developedBy"], actors_by_id)
        )
        developed_element = Et.SubElement(file_format, q("Developers"))
        add_text_element(developed_element, "DeveloperID", developer_id)

        add_text_element(developed_element, "DeveloperName", developer_name)
        add_text_element(developed_element, "OrganisationName", developer_org)
        add_text_element(
            developed_element, "DeveloperCompoundName", developer_compound_name
        )

    if format_json.get("supportedBy"):
        supported_id, supported_name, supported_org, supported_compound_name = (
            create_concatenated_actor(format_json["supportedBy"], actors_by_id)
        )
        supported_element = Et.SubElement(file_format, q("Support"))
        add_text_element(supported_element, "SupportID", supported_id)

        add_text_element(supported_element, "SupportName", supported_name)
        add_text_element(supported_element, "OrganisationName", supported_org)
        add_text_element(
            supported_element, "SupportCompoundName", supported_compound_name
        )

    for external_signature in format_json.get("externalSignatures", []):
        external_signature_element = Et.SubElement(file_format, q("ExternalSignature"))
        add_text_element(
            external_signature_element,
            "Signature",
            external_signature.get("externalSignature"),
        )
        add_text_element(
            external_signature_element,
            "SignatureType",
            external_signature.get("signatureType"),
        )

    for internal_signature in format_json.get("internalSignatures", []):
        internal_signature_element = Et.SubElement(file_format, q("InternalSignature"))
        add_text_element(
            internal_signature_element,
            "SignatureID",
            internal_signature.get("signatureID"),
        )
        add_text_element(
            internal_signature_element, "SignatureName", internal_signature.get("name")
        )
        add_text_element(
            internal_signature_element, "SignatureNote", internal_signature.get("note")
        )

        for byte_sequence in internal_signature.get("byteSequences", []):
            byte_sequence_element = Et.SubElement(
                internal_signature_element, q("ByteSequence")
            )
            add_text_element(
                byte_sequence_element, "ByteSequenceID", byte_sequence["byteSequenceID"]
            )
            add_text_element(
                byte_sequence_element, "PositionType", byte_sequence.get("positionType")
            )
            add_text_element(
                byte_sequence_element, "Offset", byte_sequence.get("offset")
            )

            add_text_element(
                byte_sequence_element, "MaxOffset", byte_sequence.get("maxOffset")
            )
            add_text_element(byte_sequence_element, "IndirectOffsetLocation", None)
            add_text_element(byte_sequence_element, "IndirectOffsetLength", None)
            add_text_element(
                byte_sequence_element, "Endianness", byte_sequence.get("endianness")
            )
            add_text_element(
                byte_sequence_element,
                "ByteSequenceValue",
                byte_sequence.get("byteSequence"),
            )

    for relationship in format_json.get("relationships", []):
        related_format_element = Et.SubElement(file_format, q("RelatedFormat"))
        add_text_element(
            related_format_element,
            "RelationshipType",
            relationship.get("relationshipType"),
        )
        add_text_element(
            related_format_element,
            "RelatedFormatID",
            relationship.get("relatedFormatID"),
        )
        add_text_element(
            related_format_element,
            "RelatedFormatName",
            relationship.get("relatedFormatName"),
        )
        add_text_element(
            related_format_element,
            "RelatedFormatVersion",
            signatures_by_id[relationship["relatedFormatID"]].get("version"),
        )

    return file_format


def convert_json_file(
    format_json, output_path: Path, actors_by_id: dict, signatures_by_id: dict
) -> None:
    root = Et.Element(q("PRONOM-Report"))
    report_format_detail = Et.SubElement(root, q("report_format_detail"))
    report_format_detail.append(
        build_file_format_element(format_json, actors_by_id, signatures_by_id)
    )

    Et.indent(root, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Et.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)


def run() -> None:
    signatures_dir = Path(sys.argv[1])
    source_dirs = ["fmt", "x-fmt"]
    output_root = Path("site")
    actors_by_id = {}
    signatures_by_id = {}
    actors_path = signatures_dir / "actors"
    for actor in os.listdir(actors_path):
        with open(actors_path / Path(actor)) as a:
            actor_json = json.load(a)
            actors_by_id[actor_json["actorId"]] = actor_json

    for source_dir in source_dirs:
        source_path = signatures_dir / "signatures" / source_dir
        for file in os.listdir(source_path):
            with open(source_path / Path(file)) as s:
                signature_json = json.load(s)
                signatures_by_id[signature_json["fileFormatID"]] = signature_json

    for signature_json in signatures_by_id.values():
        puid = next(
            idf["identifierText"]
            for idf in signature_json["identifiers"]
            if idf["identifierType"] == "PUID"
        )
        xml_file = output_root / Path(f"{puid}.xml")
        convert_json_file(signature_json, xml_file, actors_by_id, signatures_by_id)


if __name__ == "__main__":
    run()

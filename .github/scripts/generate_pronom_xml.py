#!/usr/bin/env python3

import json
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


def build_file_format_element(format_json: dict) -> Et.Element:
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
    add_text_element(file_format, "ByteOrders", format_json.get("byteOrders"))
    add_text_element(file_format, "ReleaseDate", format_json.get("releaseDate"))
    add_text_element(file_format, "WithdrawnDate", format_json.get("withdrawnDate"))
    add_text_element(
        file_format, "ProvenanceSourceID", format_json.get("formatSourceID")
    )
    add_text_element(
        file_format, "ProvenanceName", format_json.get("provenanceCompoundName")
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

    for external_signature in format_json.get("externalSignatures", []):
        external_signature_element = Et.SubElement(file_format, q("ExternalSignature"))
        add_text_element(external_signature_element, "ExternalSignatureID", None)
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
            add_text_element(byte_sequence_element, "ByteSequenceID", 1)
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
        add_text_element(related_format_element, "RelatedFormatVersion", None)

    return file_format


def convert_json_file(input_path: Path, output_path: Path) -> None:
    with input_path.open("r", encoding="utf-8") as source_file:
        format_json = json.load(source_file)

    root = Et.Element(q("PRONOM-Report"))
    report_format_detail = Et.SubElement(root, q("report_format_detail"))
    report_format_detail.append(build_file_format_element(format_json))

    Et.indent(root, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Et.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)


def sorted_json_files(path: Path) -> list[Path]:
    return sorted(path.glob("*.json"), key=lambda file_path: int(file_path.stem))


def run() -> None:
    signatures_dir = Path(sys.argv[1])
    source_dirs = ["fmt", "x-fmt"]
    output_root = Path("site")

    for source_dir in source_dirs:
        source_path = signatures_dir / "signatures" / source_dir
        destination_path = output_root / source_dir
        for json_file in sorted_json_files(source_path):
            xml_file = destination_path / f"{json_file.stem}.xml"
            convert_json_file(json_file, xml_file)


if __name__ == "__main__":
    run()

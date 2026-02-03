#!/usr/bin/env python3
"""Unpack and format XML contents of Office files (.docx, .pptx, .xlsx)"""

import random
import zipfile
from pathlib import Path

import defusedxml.minidom
from loguru import logger


def unpack_document(input_file: str | Path, output_dir: str | Path) -> None:
    """Unpack an Office file and pretty-print its XML contents.

    Args:
        input_file: Path to the input Office file (.docx, .pptx, .xlsx)
        output_dir: Directory where contents should be unpacked
    """
    input_path = Path(input_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Extract all contents
    with zipfile.ZipFile(input_path) as zf:
        zf.extractall(output_path)

    # Pretty print all XML files
    xml_files = list(output_path.rglob("*.xml")) + list(output_path.rglob("*.rels"))
    for xml_file in xml_files:
        try:
            content = xml_file.read_text(encoding="utf-8")
            # Parse and pretty print
            dom = defusedxml.minidom.parseString(content)
            pretty_xml = dom.toprettyxml(indent="  ", encoding="ascii")
            # Write back
            xml_file.write_bytes(pretty_xml)
        except Exception as e:
            logger.warning(f"Failed to format {xml_file}: {e}")

    # For .docx files, suggest an RSID for tracked changes
    if str(input_path).endswith(".docx"):
        suggested_rsid = "".join(random.choices("0123456789ABCDEF", k=8))
        logger.info(f"Suggested RSID for edit session: {suggested_rsid}")

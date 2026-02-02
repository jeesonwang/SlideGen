#!/usr/bin/env python3
"""
Command line tool to validate Office document XML files against XSD schemas and tracked changes.

Usage:
    python validate.py <dir> --original <original_file>
"""

import argparse
import sys
from pathlib import Path

from .validation import DOCXSchemaValidator, PPTXSchemaValidator, RedliningValidator


def validate_document(
    unpacked_dir: str | Path,
    original_file: str | Path,
    verbose: bool = False,
) -> bool:
    """Validate Office document XML files.

    Args:
        unpacked_dir: Path to unpacked Office document directory
        original_file: Path to original file (.docx/.pptx/.xlsx)
        verbose: Enable verbose output

    Returns:
        bool: True if validation passed, False otherwise
    """
    # Validate paths
    unpacked_path = Path(unpacked_dir)
    original_path = Path(original_file)
    file_extension = original_path.suffix.lower()

    if not unpacked_path.is_dir():
        print(f"Error: {unpacked_path} is not a directory", file=sys.stderr)
        return False
    if not original_path.is_file():
        print(f"Error: {original_path} is not a file", file=sys.stderr)
        return False
    if file_extension not in [".docx", ".pptx", ".xlsx"]:
        print(f"Error: {original_path} must be a .docx, .pptx, or .xlsx file", file=sys.stderr)
        return False

    # Determine validators
    validators = []
    match file_extension:
        case ".docx":
            validators = [DOCXSchemaValidator, RedliningValidator]
        case ".pptx":
            validators = [PPTXSchemaValidator]
        case _:
            print(f"Error: Validation not supported for file type {file_extension}", file=sys.stderr)
            return False

    # Run validators
    success = True
    for V in validators:
        print(f"DEBUG: V={V}, type(V)={type(V)}")
        try:
            validator = V(unpacked_path, original_path, verbose=verbose)
            print(f"DEBUG: validator={validator}, type={type(validator)}")
            print(f"DEBUG: has validate? {hasattr(validator, 'validate')}")
            if not hasattr(validator, "validate"):
                print(f"DEBUG: dir(validator)={dir(validator)}")
        except Exception as e:
            print(f"DEBUG: Error instantiating V: {e}")
            raise e

        if not validator.validate():  # type: ignore[attr-defined]
            success = False

    return success


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Office document XML files")
    parser.add_argument(
        "unpacked_dir",
        help="Path to unpacked Office document directory",
    )
    parser.add_argument(
        "--original",
        required=True,
        help="Path to original file (.docx/.pptx/.xlsx)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    if validate_document(args.unpacked_dir, args.original, args.verbose):
        print("All validations PASSED!")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

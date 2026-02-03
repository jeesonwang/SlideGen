#!/usr/bin/env python3
"""
Command line tool to validate Office document XML files against XSD schemas and tracked changes.
"""

from pathlib import Path

from loguru import logger

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
        logger.error(f"{unpacked_path} is not a directory")
        return False
    if not original_path.is_file():
        logger.error(f"{original_path} is not a file")
        return False
    if file_extension not in [".docx", ".pptx", ".xlsx"]:
        logger.error(f"{original_path} must be a .docx, .pptx, or .xlsx file")
        return False

    # Determine validators
    validators = []
    match file_extension:
        case ".docx":
            validators = [DOCXSchemaValidator, RedliningValidator]
        case ".pptx":
            validators = [PPTXSchemaValidator]
        case _:
            logger.error(f"Validation not supported for file type {file_extension}")
            return False

    # Run validators
    success = True
    for V in validators:
        logger.debug(f"V={V}, type(V)={type(V)}")
        try:
            validator = V(unpacked_path, original_path, verbose=verbose)
            logger.debug(f"validator={validator}, type={type(validator)}")
            logger.debug(f"has validate? {hasattr(validator, 'validate')}")
            if not hasattr(validator, "validate"):
                logger.debug(f"dir(validator)={dir(validator)}")
        except Exception as e:
            logger.debug(f"Error instantiating V: {e}")
            raise e

        if not validator.validate():  # type: ignore[attr-defined]
            success = False

    return success

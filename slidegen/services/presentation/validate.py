#!/usr/bin/env python3
"""
Command line tool to validate Office document XML files against XSD schemas.
"""

from pathlib import Path

from loguru import logger

from .validation import PPTXSchemaValidator


def validate_document(
    unpacked_dir: str | Path,
    original_file: str | Path,
    verbose: bool = False,
) -> bool:
    """Validate PowerPoint document XML files.

    Args:
        unpacked_dir: Path to unpacked document directory
        original_file: Path to original .pptx file
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
    if file_extension != ".pptx":
        logger.error(f"{original_path} must be a .pptx file")
        return False

    # Validate with PPTXSchemaValidator
    try:
        validator = PPTXSchemaValidator(unpacked_path, original_path, verbose=verbose)
    except Exception as e:
        logger.debug(f"Error instantiating PPTXSchemaValidator: {e}")
        raise e

    return validator.validate()

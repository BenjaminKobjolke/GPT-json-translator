"""
Command-line argument parser configuration for the JSON Translator.
"""
import argparse


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the JSON Translator CLI.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description='Translate JSON files to multiple languages using OpenAI GPT'
    )

    parser.add_argument(
        'input_path',
        nargs='?',
        help='Path to the source JSON file or directory (when using --translate-recursive)'
    )

    parser.add_argument(
        '--exclude-languages', '--exclude',
        help='Comma-separated list of language codes to exclude (e.g., "he,ko" or "he-IL,ko-KR")'
    )

    parser.add_argument(
        '--apply-overrides',
        action='store_true',
        help='Apply override files only, without performing translation'
    )

    parser.add_argument(
        '--translate-recursive',
        metavar='FILENAME',
        help='Recursively search for subdirectories containing FILENAME and translate if no translations exist (e.g., "en.json")'
    )

    parser.add_argument(
        '--use-cdata',
        action='store_true',
        help='For XML files: wrap string values in CDATA sections instead of escaping quotes'
    )

    return parser

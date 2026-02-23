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
        '--languages',
        help='Comma-separated list of language codes to translate to (overrides settings.ini)'
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
        '--force',
        action='store_true',
        help='With --translate-recursive: process ALL directories containing the source file, '
             'not just those without existing translations.'
    )

    parser.add_argument(
        '--use-cdata',
        action='store_true',
        help='For XML files: wrap string values in CDATA sections instead of escaping quotes'
    )

    parser.add_argument(
        '--second-input',
        metavar='PATH',
        help='Path to a second language file (e.g., de.json) for dual-language translation context. '
             'The AI uses both sources for better translations. This file will NOT be overwritten.'
    )

    # HTML/Twig extraction arguments
    parser.add_argument(
        '--extract-html',
        metavar='PATH',
        help='Extract translatable text from HTML/Twig file(s). Supports glob patterns (e.g., "templates/*.twig")'
    )

    parser.add_argument(
        '--output', '-o',
        metavar='JSON_PATH',
        help='Output JSON file path for extracted translations (required with --extract-html)'
    )

    parser.add_argument(
        '--translation-function',
        type=str,
        default='t',
        metavar='FUNC',
        help='Name of the Twig translation function (default: "t")'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating .bak backup files before modifying Twig files'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )

    return parser

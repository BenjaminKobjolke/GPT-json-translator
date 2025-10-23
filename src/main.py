"""
Main entry point for the JSON Translator.

This is a thin entry point that delegates to the CLI command handler.
All business logic has been extracted to separate modules for better
organization and maintainability.
"""
from src.cli.commands import run_translation_command


if __name__ == "__main__":
    run_translation_command()

"""
Console output utilities for the JSON Translator.
"""
from typing import Dict


def print_translation_summary(language_code: str, keys_count: int) -> None:
    """
    Print a summary of the translation task.

    Args:
        language_code: Language code being translated
        keys_count: Number of keys to translate
    """
    if keys_count > 0:
        print(f"Processing {language_code}: {keys_count} keys to translate")
    else:
        print(f"Processing {language_code}: No new keys to translate")


def print_hints_summary(global_hints: Dict[str, str], field_hints: Dict[str, str]) -> None:
    """
    Print a summary of the translation hints.

    Args:
        global_hints: Dictionary of global translation hints
        field_hints: Dictionary of field-specific translation hints
    """
    total_hints = len(global_hints) + len(field_hints)

    if total_hints > 0:
        print(f"Found {total_hints} translation hint(s):")

        if global_hints:
            print(f"  Global hints ({len(global_hints)}):")
            for key, value in global_hints.items():
                print(f"    - {key}: {value}")

        if field_hints:
            print(f"  Field-specific hints ({len(field_hints)}):")
            for field_name, hint_value in field_hints.items():
                print(f"    - {field_name}: {hint_value}")

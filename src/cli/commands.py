"""
Command handlers for the JSON Translator CLI.
"""
import os
import sys
from typing import Optional, List, Dict, Any, Tuple

from src.config import ConfigManager
from src.file_handler import FileHandler
from src.services.translation_orchestrator import TranslationOrchestrator
from src.services.override_service import OverrideService
from src.services.recursive_translator import RecursiveTranslator
from src.utils.path_utils import get_input_path, analyze_input_filename
from src.cli.argument_parser import create_argument_parser


def run_translation_command() -> None:
    """
    Main command handler for running translations.
    Routes to appropriate service based on command-line arguments.
    """
    # Print current working directory for debugging
    print(f"Current working directory: {os.getcwd()}")

    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Route to override service if --apply-overrides flag is set
    if args.apply_overrides:
        _handle_apply_overrides(args)
        return

    # Load and validate configuration
    config_manager = ConfigManager()
    if not config_manager.validate():
        sys.exit(1)

    config = config_manager.get_config()

    # Parse excluded languages if provided
    excluded_languages = _parse_excluded_languages(args.exclude_languages)

    # Route to recursive translator if --translate-recursive is set
    if args.translate_recursive:
        _handle_recursive_translation(args, config, excluded_languages)
        return

    # Handle regular single-file translation
    _handle_single_file_translation(args, config, excluded_languages)


def _handle_apply_overrides(args) -> None:
    """
    Handle the --apply-overrides command.

    Args:
        args: Parsed command-line arguments
    """
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.get_config()

    # Get input path
    input_path = get_input_path(args.input_path, config["source_path"])

    # Apply overrides
    OverrideService.apply_overrides(input_path, use_cdata=args.use_cdata)


def _handle_recursive_translation(args, config, excluded_languages: Optional[List[str]]) -> None:
    """
    Handle the --translate-recursive command.

    Args:
        args: Parsed command-line arguments
        config: Configuration dictionary
        excluded_languages: Optional list of excluded language codes
    """
    source_filename = args.translate_recursive

    # Get base directory
    base_dir = _get_base_directory(args.input_path, config.get("source_path"))

    # Get second input path if provided
    second_input_path = getattr(args, 'second_input', None)

    # Execute recursive translation
    RecursiveTranslator.find_and_translate(
        base_dir,
        source_filename,
        config,
        excluded_languages,
        use_cdata=args.use_cdata,
        second_input_path=second_input_path
    )


def _handle_single_file_translation(args, config, excluded_languages: Optional[List[str]]) -> None:
    """
    Handle regular single-file translation.

    Args:
        args: Parsed command-line arguments
        config: Configuration dictionary
        excluded_languages: Optional list of excluded language codes
    """
    # Get input path
    input_path = get_input_path(args.input_path, config["source_path"])

    # Load second input if provided
    second_input_data = _load_second_input(getattr(args, 'second_input', None))

    # Process the single file
    TranslationOrchestrator.process_single_file(
        input_path,
        config,
        excluded_languages,
        use_cdata=args.use_cdata,
        second_input_data=second_input_data
    )

    print("Translation process complete.")


def _parse_excluded_languages(exclude_arg: Optional[str]) -> Optional[List[str]]:
    """
    Parse the excluded languages argument.

    Args:
        exclude_arg: Raw exclude argument string

    Returns:
        List of excluded language codes, or None
    """
    if not exclude_arg:
        return None

    return [lang.strip() for lang in exclude_arg.split(',')]


def _get_base_directory(input_path: Optional[str], config_source_path: Optional[str]) -> str:
    """
    Determine the base directory for recursive translation.

    Args:
        input_path: Input path from command-line
        config_source_path: Source path from configuration

    Returns:
        Base directory path
    """
    if input_path:
        return input_path
    elif config_source_path:
        return os.path.dirname(config_source_path)
    else:
        return input("Enter the base directory to search: ")


def _load_second_input(second_input_path: Optional[str]) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Load and validate the second input file for dual-language translation.

    Args:
        second_input_path: Path to the second language file

    Returns:
        Tuple of (second_input_json, second_language_code) or None if not provided
    """
    if not second_input_path:
        return None

    # Validate file exists
    if not os.path.exists(second_input_path):
        print(f"Error: Second input file not found at {second_input_path}")
        sys.exit(1)

    # Analyze the filename to extract language code
    file_type, second_language, _ = analyze_input_filename(second_input_path)

    if not second_language:
        print(f"Error: Cannot determine language code from second input filename: {second_input_path}")
        print("Expected format: 'de.json', 'fr.json', 'app_de.arb', etc.")
        sys.exit(1)

    # Load the file
    try:
        second_json = FileHandler.load_json_file(second_input_path)
        print(f"Loaded second input: {second_input_path} (language: {second_language})")
        return second_json, second_language
    except Exception as e:
        print(f"Error loading second input file: {str(e)}")
        sys.exit(1)

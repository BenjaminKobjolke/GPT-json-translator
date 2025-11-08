# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GPT JSON Translator automates translation of JSON files to multiple languages using OpenAI's GPT models. The tool preserves JSON structure and handles both standard JSON localization files and Flutter ARB (Application Resource Bundle) files.

**Key capabilities:**
- Translates JSON values while preserving keys
- Supports 40+ languages
- **Full nested object support** - detects and translates new nested keys incrementally
- Recursive batch translation across directory hierarchies
- Incremental translation (only translates new/changed content)
- Translation overrides for consistent terminology
- Translation hints for proper names and context
- Concurrent translation processing for multiple languages
- Flutter ARB file support with `@@locale` metadata

## Running the Translator

### Main Translation Script
```bash
# Using virtual environment (recommended)
.\.venv\Scripts\python.exe json_translator.py path/to/source.json

# Or directly
python json_translator.py path/to/source.json

# Uses settings.ini default if no path provided
python json_translator.py

# Exclude specific languages from translation
python json_translator.py path/to/source.json --exclude-languages="he,ko,ar"
# Short alias also available
python json_translator.py path/to/source.json --exclude="he,ko"

# Recursive translation: process all subdirectories containing source file
python json_translator.py "path/to/base/directory" --translate-recursive="en.json"
# Only translates directories with ONLY the source file (no existing translations)
# Combine with exclusions
python json_translator.py "D:\release-notes\" --translate-recursive="en.json" --exclude="he,ko"
```

### JSON Attribute Remover
Removes specified attributes from all translated JSON files (excluding source files):
```bash
# Basic usage - directory mode
python json_attribute_remover.py path/to/directory path/to/attributes_to_remove.json

# File mode - processes all JSON files in the directory except the specified file
python json_attribute_remover.py path/to/en.json path/to/attributes_to_remove.json

# Specify custom source file to exclude in directory mode
python json_attribute_remover.py path/to/directory attributes.json --exclude-source="app_en.arb"

# Get help
python json_attribute_remover.py --help
```

**Attributes file format:**

The attributes file supports two formats:

1. **Simple list** (removes top-level keys only):
```json
["key1", "key2", "key3"]
```

2. **Nested object** (supports nested key removal):
```json
{
  "topLevelKey": true,
  "errors": true,
  "settings": {
    "theme": true,
    "language": true
  },
  "viewSettings": "*"
}
```

**Format rules:**
- Use `true` to remove an entire key/block
- Use `"*"` to remove all nested keys under a parent
- Use nested objects `{}` to specify which nested keys to remove
- **Important:** Empty objects `{}` won't remove anything - use `true` instead

**Examples:**

Remove entire "errors" block:
```json
{"errors": true}
```

Remove specific nested keys only:
```json
{
  "settings": {
    "theme": true,
    "advanced": true
  }
}
```

Remove all keys under "deprecated":
```json
{"deprecated": "*"}
```

### Batch Files
Multiple `.bat` files exist for different projects. These use the virtual environment and pass project-specific paths:
```bat
call .\.venv\Scripts\python.exe json_translator.py "path\to\source.json"
```

## Configuration

The tool uses `settings.ini` for configuration. Copy `settings_example.ini` to create your own:

```ini
[General]
api_key = your-openai-api-key
source_path = ./locales/en.json  # Optional default path
model = gpt-4o-mini              # OpenAI model to use

[Languages]
# Uncomment to limit languages, otherwise translates to all 40+ supported
# languages = de-DE, fr-FR, es-ES, it-IT
```

If `settings.ini` is missing required values, the tool falls back to legacy `config.py` for backward compatibility.

## Architecture

### Modular Structure
```
json_translator.py          # Entry point wrapper
json_attribute_remover.py   # Utility to remove attributes from translations
src/
├── main.py                 # Thin entry point (delegates to CLI)
├── config.py               # ConfigManager - loads settings.ini
├── translator.py           # TranslationService - OpenAI API integration
├── file_handler.py         # FileHandler - all file I/O operations
├── models/
│   └── translation_data.py # TranslationData, TranslationResult models
├── services/               # Business logic services
│   ├── translation_orchestrator.py  # Coordinates translation workflow
│   ├── override_service.py          # Applies override files
│   └── recursive_translator.py      # Handles recursive translation
├── cli/                    # Command-line interface
│   ├── argument_parser.py  # CLI argument definitions
│   └── commands.py         # Command handlers and routing
└── utils/                  # Utility functions
    ├── path_utils.py       # Path resolution and file analysis
    ├── language_utils.py   # Language code manipulation
    ├── output_utils.py     # Console output formatting
    ├── file_discovery.py   # File system discovery
    └── dict_utils.py       # Deep comparison and merge for nested objects
```

### Core Flow

The application follows a layered architecture with clear separation of concerns:

**Entry Point (src/main.py → src/cli/commands.py)**
1. **main.py** delegates to **run_translation_command()**
2. **argument_parser.create_argument_parser()** configures CLI arguments
3. **commands.py** routes to appropriate service based on flags:
   - `--apply-overrides` → **OverrideService.apply_overrides()**
   - `--translate-recursive` → **RecursiveTranslator.find_and_translate()**
   - Default → **TranslationOrchestrator.process_single_file()**

**Override Mode (OverrideService)**
- Discovers override files in `_overrides/` directory
- Merges overrides with existing translations
- No API calls, pure file operations

**Recursive Mode (RecursiveTranslator)**
1. **find_directories_with_source_file()** searches directory tree
2. **has_only_source_file()** filters to untranslated directories
3. Calls **TranslationOrchestrator.process_single_file()** for each directory

**Single File Mode (TranslationOrchestrator)**
1. **path_utils.analyze_input_filename()** detects file type (JSON/ARB)
2. **FileHandler.load_json_file()** loads source content
3. **language_utils** filters excluded and source languages
4. **TranslationData** extracts hints and prepares data
5. **TranslationService** performs translation via OpenAI API
6. **ThreadPoolExecutor** processes languages concurrently
7. **FileHandler.save_translation_result()** writes output files

### File Type Support
- **Standard JSON**: Files like `en.json`, outputs `de.json`, `fr.json`, etc.
- **Flutter ARB**: Files like `app_en.arb`, outputs `app_de.arb`, `app_fr.arb`, etc.
  - Pattern detected via regex: `^(.*?)_([a-zA-Z]{2}(?:_[a-zA-Z]{2})?)\.arb$`
  - Automatically includes `@@locale` metadata in output
  - Skips `@@locale` key during translation

### Translation Logic
- **Global Hints**: Keys like `_hint_` provide general context to GPT for all translations
- **Field-Specific Hints**: Keys like `_hint_short_description` provide context for specific fields
- **Overrides**: Files in `_overrides/{lang}.json` force specific translations, taking precedence
- **Incremental**: Only translates keys missing from existing translations or overrides
- **Nested Object Support**: Uses deep comparison (`deep_diff`) to detect missing nested keys
  - When a nested object like `viewSettings` exists but has new nested keys (e.g., `mediaViewer`), only the new keys are sent for translation
  - Deep merging (`deep_merge`) preserves all existing nested keys while adding new translations
  - Works recursively for any level of nesting
- **Merging**: Final output = existing translations + new translations + overrides (overrides win)
  - All merging operations use deep merge to preserve nested structures

### Language Code Handling
- Config uses full codes (`de-DE`, `fr-FR`)
- Internal parsing extracts base code (`de`, `fr`) via `parse_language_code()`
- ARB files use base code in filenames (`app_de.arb`) and `@@locale` values
- Standard JSON uses full code in filenames (`de-DE.json`)

### Language Exclusion
- **Command-line flag**: `--exclude-languages="he,ko"` or `--exclude="he,ko"`
- Accepts both short (`he`) and full codes (`he-IL`)
- Filters languages by comparing base codes (so `he` excludes `he-IL`)
- Applied after loading config, before creating TranslationData
- Useful when settings.ini has no languages specified (translates all by default)

## Directory Structure Expectations

```
project/
├── locales/                # Or any directory containing translations
│   ├── en.json             # Source file (standard JSON)
│   ├── de.json             # German translation
│   ├── fr.json             # French translation
│   └── _overrides/         # Optional overrides
│       ├── de.json         # German overrides
│       └── fr.json         # French overrides
```

For ARB files:
```
project/
├── lib/l10n/              # Flutter convention
│   ├── app_en.arb         # Source file
│   ├── app_de.arb         # German translation
│   └── _overrides/
│       └── app_de.arb     # German overrides
```

## Translation Hints Examples

### Global Hints
Global hints apply to all fields in the translation:
```json
{
  "_hint_": "If the language has a formal and an informal way, use the informal way.",
  "title": "Welcome to our app",
  "description": "Your AI assistant"
}
```

### Field-Specific Hints
Field-specific hints provide targeted guidance for individual fields:
```json
{
  "_hint_": "SUMMERA AI is a proper name and should not be translated",
  "short_description": "Explorer with editing, favorites & smart file management",
  "_hint_short_description": "Maximum length is 60 characters, shorten if too long by not adhering 100% to the original language",
  "app_name": "File Explorer Pro",
  "welcome_message": "Welcome to our application!"
}
```

When translating, GPT receives both types of hints:
```
Translation hints:
- If the language has a formal and an informal way, use the informal way.

Field-specific hints:
- short_description: Maximum length is 60 characters, shorten if too long by not adhering 100% to the original language
```

All hints are sent to GPT for context but excluded from output files.

## Error Handling

- **ConfigManager** validates API key presence before proceeding
- **FileHandler** raises specific exceptions: FileNotFoundError, PermissionError, JSONDecodeError
- Translation errors for one language don't block others (concurrent processing)
- Invalid JSON responses from OpenAI return empty dict, allowing process to continue
- ARB files without valid patterns fall back to JSON mode with warnings

## Code Organization Patterns

### Design Principles Applied
The codebase follows modern Python best practices:

1. **DRY (Don't Repeat Yourself)**
   - `FileHandler._get_language_filename()` centralizes filename generation logic
   - `ConfigManager._get_config_value()` handles safe config retrieval
   - `TranslationService._format_hints()` extracts hint formatting

2. **Single Responsibility Principle**
   - Each class has one primary responsibility
   - Methods are focused and typically under 35 lines
   - Helper methods extracted for reusable logic

3. **Type Safety**
   - Comprehensive type hints throughout (95%+ coverage)
   - Uses `Literal['json', 'arb']` for type constraints
   - `Optional[T]` for nullable values

4. **Error Handling Strategy**
   - Specific exception types (FileNotFoundError, JSONDecodeError, ValueError)
   - Graceful degradation: errors in one language don't block others
   - Descriptive error messages with context

### Key Implementation Details

**Services Layer** (src/services/)
- **TranslationOrchestrator**: Coordinates translation workflow, manages concurrent execution
- **OverrideService**: Handles override file application without translation
- **RecursiveTranslator**: Manages batch processing of directory hierarchies
- All services are stateless with static methods for easy testing

**CLI Layer** (src/cli/)
- **argument_parser**: Centralized argument configuration using argparse
- **commands**: Routes commands to appropriate services, handles flow control
- Clean separation between CLI concerns and business logic

**Utilities** (src/utils/)
- **path_utils**: Path resolution and filename analysis (file type detection)
- **language_utils**: Language code parsing and filtering logic
- **output_utils**: Console output formatting and summaries
- **file_discovery**: File system traversal and pattern matching
- All utilities are pure functions with no side effects

**Core Components**
- **FileHandler** (src/file_handler.py): All file I/O operations, consistent error handling
- **TranslationService** (src/translator.py): OpenAI API integration, hint formatting
- **ConfigManager** (src/config.py): Configuration loading with fallback support
- **TranslationData** (src/models/): Data models for translation workflow

**JSON Attribute Remover** (json_attribute_remover.py)
- Uses `pathlib.Path` for modern path handling
- Functional decomposition: load → filter → process → save
- Returns statistics (files processed, attributes removed)
- Configurable source file exclusion via `--exclude-source`

### Concurrency Model
- Uses `concurrent.futures.ThreadPoolExecutor` for parallel language processing
- Each language translation is independent (no shared state)
- Thread-safe file operations (each language writes to different file)
- Errors isolated per language (one failure doesn't affect others)

### Data Flow

**Command Routing (CLI Layer)**
```
main.py → run_translation_command()
        → create_argument_parser().parse_args()
        → Route based on flags:
           ├─ --apply-overrides → OverrideService
           ├─ --translate-recursive → RecursiveTranslator
           └─ default → TranslationOrchestrator
```

**Single File Translation (TranslationOrchestrator)**
```
process_single_file()
  ├─ path_utils.analyze_input_filename()
  ├─ FileHandler.load_json_file()
  ├─ language_utils.filter_excluded_languages()
  ├─ language_utils.filter_source_language()
  ├─ TranslationData (extracts hints)
  ├─ ThreadPoolExecutor.submit()
  │   └─ For each language:
  │       ├─ process_language()
  │       ├─ FileHandler.load_existing_translations()
  │       ├─ FileHandler.load_overrides()
  │       ├─ TranslationService.filter_keys_for_translation()
  │       ├─ TranslationService.translate() (OpenAI API)
  │       └─ TranslationResult (merge)
  └─ FileHandler.save_translation_result()
```

**Recursive Translation (RecursiveTranslator)**
```
find_and_translate()
  ├─ file_discovery.find_directories_with_source_file()
  ├─ file_discovery.has_only_source_file() (filter)
  └─ For each directory:
      └─ TranslationOrchestrator.process_single_file()
```

**Override Application (OverrideService)**
```
apply_overrides()
  ├─ file_discovery.discover_override_files()
  └─ For each override:
      ├─ FileHandler.load_overrides()
      ├─ FileHandler.load_existing_translations()
      ├─ TranslationResult (merge without translation)
      └─ FileHandler.save_translation_result()
```

## Development Notes

- OpenAI API uses `response_format={"type": "json_object"}` for structured output
- System prompt emphasizes translating values only, not keys
- UTF-8 encoding enforced throughout for international character support
- argparse used for CLI interfaces (supports `--help` flag)
- All file I/O operations go through FileHandler for consistency

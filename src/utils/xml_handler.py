"""
Android XML string file handling utilities.
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
import os
import copy


def load_android_xml(file_path: str) -> Tuple[Dict[str, Any], ET.Element]:
    """
    Load an Android strings.xml file and extract translatable strings.

    Args:
        file_path: Path to the XML file

    Returns:
        Tuple of (translatable_strings_dict, original_tree_root)
        The dict maps string names to their values.
        Elements with translatable="false" are excluded.

    Raises:
        FileNotFoundError: If the file doesn't exist
        ET.ParseError: If the XML is malformed
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"XML file not found: {file_path}")

    tree = ET.parse(file_path)
    root = tree.getroot()

    translatable_dict = extract_translatable_strings(root)
    return translatable_dict, root


def extract_translatable_strings(root: ET.Element) -> Dict[str, Any]:
    """
    Extract translatable string elements from XML root.

    Supports:
    - <string name="key">value</string>
    - <string-array name="key"><item>v1</item><item>v2</item></string-array>
    - <plurals name="key"><item quantity="one">1</item><item quantity="other">%d</item></plurals>

    Args:
        root: XML ElementTree root element

    Returns:
        Dictionary mapping string 'name' attributes to their values:
        - Simple strings: {"key": "value"}
        - String arrays: {"key": ["item1", "item2"]}
        - Plurals: {"key": {"one": "1 item", "other": "%d items"}}
        Elements with translatable="false" are excluded entirely.
    """
    result = {}

    for elem in root:
        # Skip elements marked as non-translatable
        if elem.get('translatable') == 'false':
            continue

        name = elem.get('name')
        if not name:
            continue

        if elem.tag == 'string':
            # Simple string element
            result[name] = elem.text or ''

        elif elem.tag == 'string-array':
            # String array: list of items
            items = []
            for item in elem.findall('item'):
                items.append(item.text or '')
            result[name] = items

        elif elem.tag == 'plurals':
            # Plurals: dict mapping quantity to text
            plurals = {}
            for item in elem.findall('item'):
                quantity = item.get('quantity')
                if quantity:
                    plurals[quantity] = item.text or ''
            result[name] = plurals

    return result


def build_translated_xml(
    source_root: ET.Element,
    translations: Dict[str, Any]
) -> ET.Element:
    """
    Build a translated XML tree from source structure and translations.

    Only includes translatable elements (excludes translatable="false").

    Args:
        source_root: Original XML root (for structure reference)
        translations: Dictionary of translated string values

    Returns:
        New XML Element tree with translated content
    """
    # Create new root element
    new_root = ET.Element('resources')

    for elem in source_root:
        # Skip non-translatable elements entirely
        if elem.get('translatable') == 'false':
            continue

        name = elem.get('name')
        if not name:
            continue

        if elem.tag == 'string' and name in translations:
            new_elem = ET.SubElement(new_root, 'string')
            new_elem.set('name', name)
            new_elem.text = translations[name]

        elif elem.tag == 'string-array' and name in translations:
            new_elem = ET.SubElement(new_root, 'string-array')
            new_elem.set('name', name)
            items = translations[name]
            if isinstance(items, list):
                for item_text in items:
                    item_elem = ET.SubElement(new_elem, 'item')
                    item_elem.text = item_text

        elif elem.tag == 'plurals' and name in translations:
            new_elem = ET.SubElement(new_root, 'plurals')
            new_elem.set('name', name)
            plurals = translations[name]
            if isinstance(plurals, dict):
                for quantity, text in plurals.items():
                    item_elem = ET.SubElement(new_elem, 'item')
                    item_elem.set('quantity', quantity)
                    item_elem.text = text

    return new_root


def save_android_xml(root: ET.Element, file_path: str, use_cdata: bool = False) -> None:
    """
    Save XML element tree to file with proper formatting.

    Args:
        root: XML root element to save
        file_path: Destination path
        use_cdata: If True, wrap string values in CDATA sections.
                   If False (default), escape quotes with backslashes.
    """
    # Ensure the directory exists
    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    # Write XML manually
    lines = ['<?xml version="1.0" encoding="utf-8"?>']
    lines.append('<resources>')

    for elem in root:
        name = elem.get('name')
        if not name:
            continue

        if elem.tag == 'string':
            text = elem.text or ''
            formatted_text = _format_text(text, use_cdata)
            lines.append(f'    <string name="{_escape_attr(name)}">{formatted_text}</string>')

        elif elem.tag == 'string-array':
            lines.append(f'    <string-array name="{_escape_attr(name)}">')
            for item in elem.findall('item'):
                text = item.text or ''
                formatted_text = _format_text(text, use_cdata)
                lines.append(f'        <item>{formatted_text}</item>')
            lines.append('    </string-array>')

        elif elem.tag == 'plurals':
            lines.append(f'    <plurals name="{_escape_attr(name)}">')
            for item in elem.findall('item'):
                quantity = item.get('quantity', '')
                text = item.text or ''
                formatted_text = _format_text(text, use_cdata)
                lines.append(f'        <item quantity="{_escape_attr(quantity)}">{formatted_text}</item>')
            lines.append('    </plurals>')

    lines.append('</resources>')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def _format_text(text: str, use_cdata: bool) -> str:
    """
    Format text for XML output.

    Args:
        text: The text content to format
        use_cdata: If True, wrap in CDATA. If False, escape quotes.

    Returns:
        Formatted text suitable for XML element content
    """
    if use_cdata:
        return f'<![CDATA[{text}]]>'
    else:
        return _escape_text(text)


def _escape_text(text: str) -> str:
    """
    Escape special characters in XML text content.

    Escapes quotes with backslashes for Android string resources.

    Args:
        text: Text to escape

    Returns:
        Escaped string safe for XML text content
    """
    # Escape quotes with backslashes (Android convention)
    text = text.replace("'", "\\'")
    text = text.replace('"', '\\"')
    # Also escape standard XML entities
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _escape_attr(value: str) -> str:
    """
    Escape special characters in XML attribute values.

    Args:
        value: Attribute value to escape

    Returns:
        Escaped string safe for XML attributes
    """
    return (value
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    """
    Add indentation to XML elements for pretty printing.

    Args:
        elem: XML element to indent
        level: Current indentation level
    """
    indent = "\n" + "    " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "    "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            _indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


def get_xml_output_path(source_path: str, language_code: str) -> str:
    """
    Calculate the output path for a translated XML file.

    Android convention:
    - Source: res/values/strings.xml
    - German: res/values-de/strings.xml
    - French: res/values-fr/strings.xml

    Args:
        source_path: Path to source strings.xml
        language_code: Target language code (e.g., 'de-DE' or 'de')

    Returns:
        Full path to output file
    """
    source_path = Path(source_path)
    filename = source_path.name  # e.g., 'strings.xml'
    parent_dir = source_path.parent  # e.g., '.../values'

    # Extract base language code (de from de-DE)
    base_lang = language_code.split('-')[0]

    # Build new directory name: values -> values-de
    new_dir_name = f"values-{base_lang}"

    # Build full output path: parent_of_values / values-de / strings.xml
    output_path = parent_dir.parent / new_dir_name / filename

    return str(output_path)


def get_xml_override_path(source_path: str, language_code: str) -> str:
    """
    Calculate the override file path for XML translations.

    Override structure:
    - Source: res/values/strings.xml
    - Override: res/values/_overrides/values-de/strings.xml

    Args:
        source_path: Path to source strings.xml
        language_code: Target language code

    Returns:
        Path to override file
    """
    source_path = Path(source_path)
    filename = source_path.name
    parent_dir = source_path.parent  # values/

    base_lang = language_code.split('-')[0]
    override_dir = f"values-{base_lang}"

    override_path = parent_dir / "_overrides" / override_dir / filename
    return str(override_path)


def load_existing_xml_translations(source_path: str, language_code: str) -> Dict[str, Any]:
    """
    Load existing XML translations for a specific language.

    Args:
        source_path: Path to source strings.xml
        language_code: Target language code

    Returns:
        Dictionary of existing translations, or empty dict if none exist
    """
    output_path = get_xml_output_path(source_path, language_code)

    if os.path.exists(output_path):
        try:
            translations, _ = load_android_xml(output_path)
            return translations
        except (ET.ParseError, IOError) as e:
            print(f"Error loading existing XML translations for {language_code}: {e}")
            return {}
    return {}


def load_xml_overrides(source_path: str, language_code: str) -> Dict[str, Any]:
    """
    Load XML override values for a specific language.

    Args:
        source_path: Path to source strings.xml
        language_code: Target language code

    Returns:
        Dictionary of override values, or empty dict if none exist
    """
    override_path = get_xml_override_path(source_path, language_code)

    if os.path.exists(override_path):
        try:
            overrides, _ = load_android_xml(override_path)
            return overrides
        except (ET.ParseError, IOError) as e:
            print(f"Error loading XML overrides for {language_code}: {e}")
            return {}
    return {}


def merge_xml_translations(
    existing: Dict[str, Any],
    translated: Dict[str, Any],
    overrides: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge XML translations with existing content and overrides.

    Priority: overrides > translated > existing

    Args:
        existing: Existing translations
        translated: Newly translated content
        overrides: Override values

    Returns:
        Merged dictionary
    """
    result = existing.copy()
    result.update(translated)
    result.update(overrides)
    return result

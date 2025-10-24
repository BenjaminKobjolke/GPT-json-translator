"""
Test script to verify nested object translation works correctly.
"""
import json
from pathlib import Path
from src.utils.dict_utils import deep_diff, deep_merge
from src.translator import TranslationService
from src.models.translation_data import TranslationResult


def test_deep_diff():
    """Test the deep_diff function."""
    print("Testing deep_diff function...")

    # Test 1: Completely new nested key
    source = {
        "viewSettings": {
            "title": "View settings",
            "generalSettings": "GENERAL SETTINGS",
            "mediaViewer": "MEDIA VIEWER"
        }
    }
    existing = {
        "viewSettings": {
            "title": "Ansichtseinstellungen",
            "generalSettings": "ALLGEMEINE EINSTELLUNGEN"
        }
    }
    result = deep_diff(source, existing)
    print(f"\nTest 1 - New nested key:")
    print(f"  Source: {json.dumps(source, indent=2)}")
    print(f"  Existing: {json.dumps(existing, indent=2)}")
    print(f"  Diff (should contain only mediaViewer): {json.dumps(result, indent=2)}")
    assert result == {"viewSettings": {"mediaViewer": "MEDIA VIEWER"}}, "Test 1 failed!"
    print("  Test 1 passed")

    # Test 2: Completely new top-level key
    source = {"newKey": "value", "existingKey": "value"}
    existing = {"existingKey": "wert"}
    result = deep_diff(source, existing)
    print(f"\nTest 2 - New top-level key:")
    print(f"  Diff (should contain only newKey): {json.dumps(result, indent=2)}")
    assert result == {"newKey": "value"}, "Test 2 failed!"
    print("  Test 2 passed")

    # Test 3: No differences
    source = {"key": "value"}
    existing = {"key": "wert"}
    result = deep_diff(source, existing)
    print(f"\nTest 3 - No differences:")
    print(f"  Diff (should be empty): {json.dumps(result, indent=2)}")
    assert result == {}, "Test 3 failed!"
    print("  Test 3 passed")

    # Test 4: Multiple nested levels
    source = {
        "level1": {
            "level2": {
                "level3": "value",
                "level3_new": "new_value"
            }
        }
    }
    existing = {
        "level1": {
            "level2": {
                "level3": "wert"
            }
        }
    }
    result = deep_diff(source, existing)
    print(f"\nTest 4 - Multiple nested levels:")
    print(f"  Diff: {json.dumps(result, indent=2)}")
    assert result == {"level1": {"level2": {"level3_new": "new_value"}}}, "Test 4 failed!"
    print("  Test 4 passed")


def test_deep_merge():
    """Test the deep_merge function."""
    print("\n\nTesting deep_merge function...")

    # Test 1: Merge nested objects
    base = {
        "viewSettings": {
            "title": "Ansichtseinstellungen",
            "generalSettings": "ALLGEMEINE EINSTELLUNGEN"
        }
    }
    updates = {
        "viewSettings": {
            "mediaViewer": "MEDIENANZEIGE"
        }
    }
    result = deep_merge(base, updates)
    print(f"\nTest 1 - Merge nested objects:")
    print(f"  Base: {json.dumps(base, indent=2)}")
    print(f"  Updates: {json.dumps(updates, indent=2)}")
    print(f"  Result: {json.dumps(result, indent=2)}")
    expected = {
        "viewSettings": {
            "title": "Ansichtseinstellungen",
            "generalSettings": "ALLGEMEINE EINSTELLUNGEN",
            "mediaViewer": "MEDIENANZEIGE"
        }
    }
    assert result == expected, "Test 1 failed!"
    print("  Test 1 passed - all nested keys preserved")

    # Test 2: Override existing nested value
    base = {"settings": {"theme": "dark", "lang": "en"}}
    updates = {"settings": {"theme": "light"}}
    result = deep_merge(base, updates)
    print(f"\nTest 2 - Override existing nested value:")
    print(f"  Result: {json.dumps(result, indent=2)}")
    assert result == {"settings": {"theme": "light", "lang": "en"}}, "Test 2 failed!"
    print("  Test 2 passed")

    # Test 3: Multiple levels
    base = {"a": {"b": {"c": 1, "d": 2}}}
    updates = {"a": {"b": {"e": 3}}}
    result = deep_merge(base, updates)
    print(f"\nTest 3 - Multiple levels:")
    print(f"  Result: {json.dumps(result, indent=2)}")
    assert result == {"a": {"b": {"c": 1, "d": 2, "e": 3}}}, "Test 3 failed!"
    print("  Test 3 passed")


def test_filter_keys_for_translation():
    """Test the filter_keys_for_translation function."""
    print("\n\nTesting filter_keys_for_translation...")

    # Simulate the bug scenario
    source_json = {
        "viewSettings": {
            "title": "View settings",
            "generalSettings": "GENERAL SETTINGS",
            "mediaViewer": "MEDIA VIEWER"
        }
    }
    existing_json = {
        "viewSettings": {
            "title": "Ansichtseinstellungen",
            "generalSettings": "ALLGEMEINE EINSTELLUNGEN"
        }
    }
    overrides = {}

    result = TranslationService.filter_keys_for_translation(
        source_json,
        existing_json,
        overrides,
        'json'
    )

    print(f"\nBug scenario test:")
    print(f"  Source: {json.dumps(source_json, indent=2)}")
    print(f"  Existing: {json.dumps(existing_json, indent=2)}")
    print(f"  Keys for translation: {json.dumps(result, indent=2)}")

    expected = {
        "viewSettings": {
            "mediaViewer": "MEDIA VIEWER"
        }
    }
    assert result == expected, f"Test failed! Expected {expected}, got {result}"
    print("  Test passed - mediaViewer correctly identified for translation")


def test_translation_result_merge():
    """Test the TranslationResult get_merged_content method."""
    print("\n\nTesting TranslationResult.get_merged_content...")

    existing_content = {
        "viewSettings": {
            "title": "Ansichtseinstellungen",
            "generalSettings": "ALLGEMEINE EINSTELLUNGEN"
        }
    }

    translated_content = {
        "viewSettings": {
            "mediaViewer": "MEDIENANZEIGE"
        }
    }

    result = TranslationResult(
        language_code="de",
        translated_content=translated_content,
        existing_content=existing_content,
        overrides={}
    )

    merged = result.get_merged_content()
    print(f"\nMerge test:")
    print(f"  Existing: {json.dumps(existing_content, indent=2)}")
    print(f"  Translated: {json.dumps(translated_content, indent=2)}")
    print(f"  Merged: {json.dumps(merged, indent=2)}")

    expected = {
        "viewSettings": {
            "title": "Ansichtseinstellungen",
            "generalSettings": "ALLGEMEINE EINSTELLUNGEN",
            "mediaViewer": "MEDIENANZEIGE"
        }
    }

    assert merged == expected, f"Test failed! Expected {expected}, got {merged}"
    print("  Test passed - all nested keys preserved in merge")


def main():
    """Run all tests."""
    print("=" * 60)
    print("NESTED OBJECT TRANSLATION FIX - TEST SUITE")
    print("=" * 60)

    try:
        test_deep_diff()
        test_deep_merge()
        test_filter_keys_for_translation()
        test_translation_result_merge()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe nested object translation bug has been fixed.")
        print("You can now run translations with new nested keys and they will be")
        print("correctly detected and translated without losing existing translations.")

    except AssertionError as e:
        print(f"\nTEST FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

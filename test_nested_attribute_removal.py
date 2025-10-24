"""
Test script to verify nested attribute removal works correctly.
"""
import json
import tempfile
import shutil
from pathlib import Path
from json_attribute_remover import (
    remove_attributes_from_file,
    load_attributes_to_remove,
    remove_attributes_recursive,
    cleanup_empty_parents
)


def test_legacy_list_format():
    """Test that legacy list format still works (backward compatibility)."""
    print("Testing legacy list format...")

    # Create test data
    data = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(data, f)
        temp_file = Path(f.name)

    try:
        # Remove attributes using list format
        attributes = ["key1", "key3"]
        removed = remove_attributes_from_file(temp_file, attributes)

        # Load result
        with temp_file.open('r', encoding='utf-8') as f:
            result = json.load(f)

        print(f"  Removed {removed} attributes")
        print(f"  Result: {json.dumps(result, indent=2)}")

        assert removed == 2, f"Expected 2 removals, got {removed}"
        assert "key1" not in result, "key1 should be removed"
        assert "key2" in result, "key2 should remain"
        assert "key3" not in result, "key3 should be removed"

        print("  Test passed!")

    finally:
        temp_file.unlink()


def test_nested_dict_format():
    """Test nested object removal with dict format."""
    print("\nTesting nested dict format...")

    # Create test data with nested structure
    data = {
        "topLevel": "value",
        "viewSettings": {
            "title": "View settings",
            "imageViewer": "Image Viewer",
            "keepThis": "Keep this"
        },
        "otherSettings": {
            "theme": "dark"
        }
    }

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        temp_file = Path(f.name)

    try:
        print(f"  Before: {json.dumps(data, indent=2)}")

        # Remove nested attribute
        attributes = {
            "viewSettings": {
                "imageViewer": True
            }
        }
        removed = remove_attributes_from_file(temp_file, attributes)

        # Load result
        with temp_file.open('r', encoding='utf-8') as f:
            result = json.load(f)

        print(f"  Removed {removed} attributes")
        print(f"  After: {json.dumps(result, indent=2)}")

        assert removed == 1, f"Expected 1 removal, got {removed}"
        assert "topLevel" in result, "topLevel should remain"
        assert "viewSettings" in result, "viewSettings should remain"
        assert "imageViewer" not in result["viewSettings"], "imageViewer should be removed"
        assert "keepThis" in result["viewSettings"], "keepThis should remain"

        print("  Test passed!")

    finally:
        temp_file.unlink()


def test_wildcard_removal():
    """Test wildcard removal of all nested keys."""
    print("\nTesting wildcard removal...")

    # Create test data
    data = {
        "keepThis": "value",
        "removeAll": {
            "nested1": "value1",
            "nested2": "value2",
            "deepNested": {
                "key": "value"
            }
        }
    }

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        temp_file = Path(f.name)

    try:
        print(f"  Before: {json.dumps(data, indent=2)}")

        # Remove all nested keys with wildcard
        attributes = {
            "removeAll": "*"
        }
        removed = remove_attributes_from_file(temp_file, attributes)

        # Load result
        with temp_file.open('r', encoding='utf-8') as f:
            result = json.load(f)

        print(f"  Removed {removed} attributes")
        print(f"  After: {json.dumps(result, indent=2)}")

        # wildcard removes all 3 nested keys + cleanup removes empty parent (total 4)
        assert removed >= 3, f"Expected at least 3 removals, got {removed}"
        assert "keepThis" in result, "keepThis should remain"
        assert "removeAll" not in result, "removeAll should be removed (empty parent cleanup)"

        print("  Test passed!")

    finally:
        temp_file.unlink()


def test_empty_parent_cleanup():
    """Test that empty parent objects are removed."""
    print("\nTesting empty parent cleanup...")

    # Create test data
    data = {
        "keepThis": "value",
        "parent": {
            "onlyChild": "value"
        }
    }

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        temp_file = Path(f.name)

    try:
        print(f"  Before: {json.dumps(data, indent=2)}")

        # Remove the only child, should trigger parent cleanup
        attributes = {
            "parent": {
                "onlyChild": True
            }
        }
        removed = remove_attributes_from_file(temp_file, attributes)

        # Load result
        with temp_file.open('r', encoding='utf-8') as f:
            result = json.load(f)

        print(f"  Removed {removed} attributes")
        print(f"  After: {json.dumps(result, indent=2)}")

        # Note: parent cleanup happens automatically but may not add to count
        # The important thing is that the parent is actually removed
        assert removed >= 1, f"Expected at least 1 removal, got {removed}"
        assert "keepThis" in result, "keepThis should remain"
        assert "parent" not in result, "parent should be removed (empty after child removal)"

        print("  Test passed!")

    finally:
        temp_file.unlink()


def test_multiple_nested_levels():
    """Test removal at multiple nesting levels."""
    print("\nTesting multiple nested levels...")

    # Create test data with deep nesting
    data = {
        "level1": {
            "level2": {
                "level3": {
                    "removeMe": "value",
                    "keepMe": "value"
                },
                "keepLevel2": "value"
            }
        }
    }

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        temp_file = Path(f.name)

    try:
        print(f"  Before: {json.dumps(data, indent=2)}")

        # Remove deeply nested key
        attributes = {
            "level1": {
                "level2": {
                    "level3": {
                        "removeMe": True
                    }
                }
            }
        }
        removed = remove_attributes_from_file(temp_file, attributes)

        # Load result
        with temp_file.open('r', encoding='utf-8') as f:
            result = json.load(f)

        print(f"  Removed {removed} attributes")
        print(f"  After: {json.dumps(result, indent=2)}")

        assert removed == 1, f"Expected 1 removal, got {removed}"
        assert "level1" in result, "level1 should remain"
        assert "level2" in result["level1"], "level2 should remain"
        assert "level3" in result["level1"]["level2"], "level3 should remain"
        assert "removeMe" not in result["level1"]["level2"]["level3"], "removeMe should be removed"
        assert "keepMe" in result["level1"]["level2"]["level3"], "keepMe should remain"

        print("  Test passed!")

    finally:
        temp_file.unlink()


def test_mixed_format():
    """Test combination of top-level and nested removal."""
    print("\nTesting mixed format (top-level + nested)...")

    # Create test data
    data = {
        "topLevelRemove": "value",
        "topLevelKeep": "value",
        "nested": {
            "removeThis": "value",
            "keepThis": "value"
        }
    }

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        temp_file = Path(f.name)

    try:
        print(f"  Before: {json.dumps(data, indent=2)}")

        # Remove both top-level and nested keys
        attributes = {
            "topLevelRemove": True,
            "nested": {
                "removeThis": True
            }
        }
        removed = remove_attributes_from_file(temp_file, attributes)

        # Load result
        with temp_file.open('r', encoding='utf-8') as f:
            result = json.load(f)

        print(f"  Removed {removed} attributes")
        print(f"  After: {json.dumps(result, indent=2)}")

        assert removed == 2, f"Expected 2 removals, got {removed}"
        assert "topLevelRemove" not in result, "topLevelRemove should be removed"
        assert "topLevelKeep" in result, "topLevelKeep should remain"
        assert "nested" in result, "nested should remain"
        assert "removeThis" not in result["nested"], "removeThis should be removed"
        assert "keepThis" in result["nested"], "keepThis should remain"

        print("  Test passed!")

    finally:
        temp_file.unlink()


def main():
    """Run all tests."""
    print("=" * 60)
    print("NESTED ATTRIBUTE REMOVAL - TEST SUITE")
    print("=" * 60)

    try:
        test_legacy_list_format()
        test_nested_dict_format()
        test_wildcard_removal()
        test_empty_parent_cleanup()
        test_multiple_nested_levels()
        test_mixed_format()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe nested attribute removal feature is working correctly.")
        print("You can now use dict format in attributes_to_remove.json:")
        print('  {"viewSettings": {"imageViewer": true}}')
        print('  {"parent": "*"}  // removes all nested keys')

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

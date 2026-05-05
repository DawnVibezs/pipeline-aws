"""
Unit tests for validator module.
"""
import pytest
from validator import validate_records


def test_validate_valid_records():
    """Test validation of valid records."""
    records = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ]
    valid, errors = validate_records(records)
    assert len(valid) == 2
    assert len(errors) == 0


def test_validate_empty_record():
    """Test validation skips empty records."""
    records = [
        {"name": "Alice"},
        {},
        {"name": "Bob"},
    ]
    valid, errors = validate_records(records)
    assert len(valid) == 2
    assert len(errors) == 1


def test_validate_non_dict_record():
    """Test validation skips non-dict records."""
    records = [
        {"name": "Alice"},
        "invalid",
        {"name": "Bob"},
    ]
    valid, errors = validate_records(records)
    assert len(valid) == 2
    assert len(errors) == 1
    assert "not a dictionary" in errors[0]["error"]

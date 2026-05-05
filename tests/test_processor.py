"""
Unit tests for processor module.
"""
import pytest
from processor import process_file, _parse_csv, _parse_json


def test_parse_csv():
    """Test CSV parsing."""
    csv_content = "name,age\nAlice,30\nBob,25"
    result = _parse_csv(csv_content)
    assert len(result) == 2
    assert result[0]["name"] == "Alice"
    assert result[1]["age"] == "25"


def test_parse_json():
    """Test JSON parsing."""
    json_content = '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]'
    result = _parse_json(json_content)
    assert len(result) == 2
    assert result[0]["name"] == "Alice"


def test_process_file_csv():
    """Test process_file with CSV."""
    csv_content = "id,value\n1,100\n2,200"
    result = process_file(csv_content, "csv")
    assert len(result) == 2


def test_process_file_json():
    """Test process_file with JSON."""
    json_content = '[{"id": "1", "value": "100"}]'
    result = process_file(json_content, "json")
    assert len(result) == 1


def test_process_file_unsupported():
    """Test process_file with unsupported type."""
    with pytest.raises(ValueError):
        process_file("content", "xml")

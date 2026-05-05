"""
Unit tests for utils module.
"""
import pytest
from utils import detect_file_type, build_job_result


def test_detect_csv():
    """Test CSV file detection."""
    assert detect_file_type("data.csv") == "csv"
    assert detect_file_type("path/to/file.csv") == "csv"


def test_detect_json():
    """Test JSON file detection."""
    assert detect_file_type("data.json") == "json"
    assert detect_file_type("path/to/file.json") == "json"


def test_detect_unsupported():
    """Test unsupported file type detection."""
    with pytest.raises(ValueError):
        detect_file_type("data.xml")
    with pytest.raises(ValueError):
        detect_file_type("data.txt")


def test_build_job_result():
    """Test job result building."""
    records = [{"id": 1}, {"id": 2}]
    errors = [{"index": 0, "error": "invalid"}]
    
    result = build_job_result("job-123", "source.csv", records, errors)
    
    assert result["job_id"] == "job-123"
    assert result["source_file"] == "source.csv"
    assert result["valid_records"] == 2
    assert result["error_count"] == 1
    assert "processed_at" in result

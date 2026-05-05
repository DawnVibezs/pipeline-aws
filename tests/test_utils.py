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
    # A chamada agora obedece os novos parâmetros da sua função no utils.py
    result = build_job_result(
        job_id="job-123",
        source_file="source.csv",
        status="SUCCESS",
        total=2,
        valid=1,
        error_count=1,
        output_key="processed/job-123.json",
        started_at="2024-01-01T10:00:00Z"
    )
    
    assert result["job_id"] == "job-123"
    assert result["status"] == "SUCCESS"
    assert "ttl" in result

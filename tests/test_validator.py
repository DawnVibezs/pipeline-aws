"""
Unit tests for validator module.
"""
import pytest
from validator import validate_records

def test_validate_valid_records():
    """Test validation of valid records."""
    records = [
        {"id": "1", "name": "Alice", "email": "alice@teste.com", "age": 30},
        {"id": "2", "name": "Bob", "email": "bob@teste.com", "age": 25},
    ]
    valid, errors = validate_records(records)
    assert len(valid) == 2
    assert len(errors) == 0

def test_validate_empty_record():
    """Test validation skips empty records."""
    records = [
        {"id": "1", "name": "Alice", "email": "alice@teste.com"},
        {},
        {"id": "2", "name": "Bob", "email": "bob@teste.com"},
    ]
    valid, errors = validate_records(records)
    assert len(valid) == 2
    assert len(errors) == 1

def test_validate_non_dict_record():
    """Test validation skips non-dict records."""
    records = [
        {"id": "1", "name": "Alice", "email": "alice@teste.com"},
        "invalid",
        {"id": "2", "name": "Bob", "email": "bob@teste.com"},
    ]
    valid, errors = validate_records(records)
    assert len(valid) == 2
    assert len(errors) == 1
    # Verifica se a mensagem de erro bate com a que criamos agora
    assert "Formato inválido" in errors[0]["errors"][0]
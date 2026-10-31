import pytest
from src.validators.accounts import validate_email


def test_validate_email_success():
    email = "test.user@example.com"
    assert validate_email(email) == email


def test_validate_email_failure():
    with pytest.raises(ValueError):
        validate_email("invalid-email-string")

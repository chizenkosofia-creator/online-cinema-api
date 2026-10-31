import pytest
from src.validators.accounts import validate_email
from src.security.password import get_password_hash, verify_password
from src.security.token import create_refresh_token


@pytest.mark.parametrize(
    "email",
    [
        "user@example.com",
        "test.name+tag@sub.domain.org",
        "user123@gmail.com",
    ],
)
def test_validate_email_success(email):
    assert validate_email(email) == email


@pytest.mark.parametrize(
    "invalid_email",
    [
        "plainstring",
        "missing-at-sign.com",
        "@missing-username.com",
        "user@.com",
        "user@domain",
    ],
)
def test_validate_email_failure(invalid_email):
    with pytest.raises(ValueError):
        validate_email(invalid_email)


def test_password_hashing_and_verification():
    raw_password = "SuperSecretPassword123!"

    hashed_password = get_password_hash(raw_password)

    assert hashed_password != raw_password
    assert isinstance(hashed_password, str)

    assert verify_password(raw_password, hashed_password) is True

    assert verify_password("WrongPassword999!", hashed_password) is False


def test_create_refresh_token():
    token = create_refresh_token()

    assert isinstance(token, str)
    assert len(token) > 0
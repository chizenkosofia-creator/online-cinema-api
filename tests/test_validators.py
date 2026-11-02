import pytest
from src.validators.accounts import validate_email


@pytest.mark.parametrize(
    "input_email, expected_email",
    [
        ("test.user@example.com", "test.user@example.com"),
        ("user@subdomain.example.co.uk", "user@subdomain.example.co.uk"),
        ("firstname.lastname@domain.org", "firstname.lastname@domain.org"),
        ("user123@gmail.com", "user123@gmail.com"),
        ("a_b_c@test-domain.com", "a_b_c@test-domain.com"),
        ("USER@EXAMPLE.COM", "USER@example.com"),
        ("user+mailbox@example.com", "user+mailbox@example.com"),
    ],
)
def test_validate_email_success(input_email: str, expected_email: str):
    assert validate_email(input_email) == expected_email


@pytest.mark.parametrize(
    "invalid_email",
    [
        "plainaddress",
        "@missingdomain.com",
        "user@.com",
        "user@domain",
        "user name@example.com",
        "user@domain..com",
        "user@domain.",
        ".user@example.com",
        "user.@example.com",
        "user@@example.com",
        "",
        "   ",
    ],
)
def test_validate_email_failure(invalid_email: str):
    with pytest.raises(ValueError):
        validate_email(invalid_email)


@pytest.mark.parametrize(
    "invalid_type_input",
    [
        None,
        12345,
        ["a@b.com"],
        {"email": "test@example.com"},
    ],
)
def test_validate_email_invalid_types(invalid_type_input):
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_email(invalid_type_input)

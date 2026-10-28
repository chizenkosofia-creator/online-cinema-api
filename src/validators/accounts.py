import re
from email_validator import validate_email as validate_email_lib, EmailNotValidError
from fastapi import HTTPException, status


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The password must contain at least 8 characters."
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль повинен містити хоча б одну велику літеру."
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The password must contain at least one lowercase letter."
        )
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The password must contain at least one digit."
        )


def validate_email(email: str) -> str:
    """Validate email syntax and normalize the email address.

    Args:
        email (str): Raw email address string from user input.

    Returns:
        str: Normalized, lowercase email address.

    Raises:
        HTTPException: HTTP 400 Bad Request if email syntax is invalid.
    """
    try:
        email_info = validate_email_lib(email, check_deliverability=False)

        return email_info.normalized
    except EmailNotValidError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email address: {str(exc)}"
        )

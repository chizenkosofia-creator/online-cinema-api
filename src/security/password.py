import bcrypt


def get_password_hash(password: str) -> str:
    if isinstance(password, str):
        password = password.encode("utf-8")[:72]
    elif isinstance(password, bytes):
        password = password[:72]

    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if isinstance(plain_password, str):
        plain_password = plain_password.encode("utf-8")[:72]
    elif isinstance(plain_password, bytes):
        plain_password = plain_password[:72]

    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode("utf-8")

    return bcrypt.checkpw(plain_password, hashed_password)

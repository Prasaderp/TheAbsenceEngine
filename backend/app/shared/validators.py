import re
from pydantic import field_validator

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email_format(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_RE.match(v):
        raise ValueError("Invalid email address.")
    if len(v) > 255:
        raise ValueError("Email too long.")
    return v


def validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if len(v) > 128:
        raise ValueError("Password too long.")
    return v


def validate_name(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Name must not be empty.")
    if len(v) > 100:
        raise ValueError("Name too long (max 100 chars).")
    return v


def strip_str(v: str) -> str:
    return v.strip() if isinstance(v, str) else v

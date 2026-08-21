import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def admin_username() -> str:
    return os.environ.get("ADMIN_USERNAME", "admin")


def admin_password() -> str:
    return os.environ.get("ADMIN_PASSWORD", "admin")


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    if os.environ.get("DISABLE_AUTH", "").lower() in {"1", "true", "yes"}:
        return "admin"
    user_ok = secrets.compare_digest(credentials.username, admin_username())
    password_ok = secrets.compare_digest(credentials.password, admin_password())
    if not (user_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": 'Basic realm="Recipe Admin"'},
        )
    return credentials.username

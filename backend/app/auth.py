# -*- coding: utf-8 -*-
"""Username / password authentication.

The application runs on an office machine or a trusted LAN, so this is
deliberately small: PBKDF2-hashed passwords in the database and a signed,
expiring bearer token. There is no third-party identity provider to configure.

A default administrator is created on first run; the credentials are printed
once at startup and should be changed from the UI.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import LOCAL_MODE, SECRET_PATH
from .db import get_db
from .models import User

DEFAULT_USERNAME = "admin"
# First-run admin password; set PENSION_DEFAULT_PASSWORD to choose your own.
DEFAULT_PASSWORD = os.environ.get("PENSION_DEFAULT_PASSWORD", "ChangeMe@123")

TOKEN_TTL_SECONDS = 12 * 60 * 60       # a working day
PBKDF2_ROUNDS = 240_000


# --------------------------------------------------------------------------
# secret key
# --------------------------------------------------------------------------
def _secret() -> bytes:
    """A per-installation signing key, so tokens survive a restart.

    Stored as hex rather than raw bytes: a random key can begin or end with a
    byte that looks like whitespace, and trimming the file would then yield a
    different key on read-back, invalidating every token already issued.
    """
    if SECRET_PATH.exists():
        try:
            value = bytes.fromhex(SECRET_PATH.read_text().strip())
            if len(value) >= 32:
                return value
        except ValueError:
            pass                        # unreadable key file; write a fresh one
    value = secrets.token_bytes(32)
    SECRET_PATH.write_text(value.hex())
    try:
        os.chmod(SECRET_PATH, 0o600)
    except OSError:
        pass                            # best effort; Windows ACLs differ
    return value


# --------------------------------------------------------------------------
# passwords
# --------------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                     bytes.fromhex(salt_hex), int(rounds))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


# --------------------------------------------------------------------------
# tokens
# --------------------------------------------------------------------------
def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def make_token(user: User) -> str:
    payload = {"sub": user.username, "uid": user.id, "role": user.role,
               "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def read_token(token: str) -> dict | None:
    try:
        body, signature = token.split(".")
        expected = _b64(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(_unb64(body))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload


# --------------------------------------------------------------------------
# dependencies
# --------------------------------------------------------------------------
_bearer = HTTPBearer(auto_error=False)


LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def local_mode_user(request: Request, db: Session) -> User | None:
    """The administrator account, when this is a desktop run on this machine.

    Two conditions must both hold: the operator asked for it (PENSION_LOCAL_MODE,
    which start.bat sets) and the request came from the loopback interface. A
    request arriving over the network is never trusted this way, so switching the
    flag on by mistake on a server still leaves the sign-in in place.
    """
    if not LOCAL_MODE:
        return None
    client = request.client.host if request.client else ""
    if client not in LOOPBACK:
        return None
    return (db.query(User).filter(User.role == "admin").order_by(User.id).first())


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the signed-in user, from the Authorization header or the cookie."""
    token = credentials.credentials if credentials else request.cookies.get("session")
    payload = read_token(token) if token else None
    if not payload:
        local = local_mode_user(request, db)
        if local is not None:
            return local
        raise HTTPException(401, "Sign in to continue")
    user = db.get(User, payload.get("uid"))
    if user is None or user.username != payload.get("sub"):
        raise HTTPException(401, "Sign in to continue")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "This action needs an administrator account")
    return user


def ensure_default_user(db: Session) -> User | None:
    """Create the initial administrator the first time the app runs."""
    if db.query(User).count():
        return None
    user = User(
        username=DEFAULT_USERNAME,
        display_name="Administrator",
        password_hash=hash_password(DEFAULT_PASSWORD),
        role="admin",
        must_change_password=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

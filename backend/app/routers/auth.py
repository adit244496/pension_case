"""Sign in, sign out, and account management."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import (DEFAULT_PASSWORD, TOKEN_TTL_SECONDS, current_user,
                    hash_password, make_token, require_admin, verify_password)
from ..db import get_db
from ..models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    display_name: str = ""
    password: str = Field(min_length=8)
    role: str = "operator"


def _profile(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name or user.username,
        "role": user.role,
        "must_change_password": bool(user.must_change_password),
        "using_default_password": verify_password(DEFAULT_PASSWORD, user.password_hash),
    }


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username.strip()).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        # Same message either way, so the form cannot be used to find valid names.
        raise HTTPException(401, "Incorrect username or password")

    user.last_login_at = datetime.utcnow()
    db.commit()

    token = make_token(user)
    response.set_cookie("session", token, httponly=True, samesite="lax",
                        max_age=TOKEN_TTL_SECONDS)
    return {"token": token, "expires_in": TOKEN_TTL_SECONDS, "user": _profile(user)}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"status": "signed out"}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return _profile(user)


@router.post("/password")
def change_password(payload: PasswordChange, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, "The current password is not correct")
    if payload.new_password == payload.current_password:
        raise HTTPException(400, "The new password must be different")
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    db.commit()
    return {"status": "password changed"}


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [_profile(u) for u in db.query(User).order_by(User.username).all()]


@router.post("/users", status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db),
                _: User = Depends(require_admin)):
    username = payload.username.strip()
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(409, f"A user named '{username}' already exists")
    if payload.role not in ("admin", "operator"):
        raise HTTPException(400, "Role must be 'admin' or 'operator'")
    user = User(username=username, display_name=payload.display_name or username,
                password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _profile(user)


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db),
                admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "You cannot delete the account you are signed in with")
    if user.role == "admin" and db.query(User).filter(User.role == "admin").count() <= 1:
        raise HTTPException(400, "At least one administrator account must remain")
    db.delete(user)
    db.commit()

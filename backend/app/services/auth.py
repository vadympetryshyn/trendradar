import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.email import send_password_reset_email, send_verification_email
from app.utils.security import create_access_token, hash_password, verify_password


async def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


async def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


async def register_user(
    db: Session,
    email: str,
    password: str,
    name: Optional[str] = None,
) -> User:
    existing_user = await get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    verification_token = secrets.token_urlsafe(32)

    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
        is_email_verified=False,
        email_verification_token=verification_token,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    await send_verification_email(email, verification_token)

    return user


async def authenticate_user(db: Session, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return user


async def authenticate_google(db: Session, google_token: str) -> User:
    if google_token.startswith("ya29."):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {google_token}"},
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google access token",
                    )
                userinfo = response.json()

            google_id = userinfo.get("sub")
            email = userinfo.get("email")
            name = userinfo.get("name")

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to verify Google token: {str(e)}",
            )
    else:
        try:
            idinfo = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                settings.google_oauth_client_id,
            )

            google_id = idinfo.get("sub")
            email = idinfo.get("email")
            name = idinfo.get("name")

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(e)}",
            )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not provided by Google",
        )

    # Check if user exists by google_id
    user = db.query(User).filter(User.google_id == google_id).first()

    if user:
        if name and user.name != name:
            user.name = name
        db.commit()
        return user

    # Check if user exists by email
    user = await get_user_by_email(db, email)

    if user:
        user.google_id = google_id
        if not user.name and name:
            user.name = name
        user.is_email_verified = True
        db.commit()
        return user

    # Block new-user creation when registration is disabled
    if not settings.registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently closed. Please log in with an existing account.",
        )

    # Create new user
    user = User(
        email=email,
        google_id=google_id,
        name=name,
        is_email_verified=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


async def verify_email(db: Session, token: str) -> User:
    user = db.query(User).filter(User.email_verification_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired verification token",
        )

    user.is_email_verified = True
    user.email_verification_token = None
    db.commit()
    db.refresh(user)

    return user


async def request_password_reset(db: Session, email: str) -> None:
    user = await get_user_by_email(db, email)

    if not user:
        return

    reset_token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=1)

    user.password_reset_token = reset_token
    user.password_reset_expires = expires
    db.commit()

    await send_password_reset_email(email, reset_token)


async def reset_password(db: Session, token: str, new_password: str) -> User:
    user = db.query(User).filter(User.password_reset_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired reset token",
        )

    if user.password_reset_expires and user.password_reset_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired reset token",
        )

    user.password_hash = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    db.refresh(user)

    return user


async def resend_verification_email(db: Session, email: str) -> None:
    user = await get_user_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    verification_token = secrets.token_urlsafe(32)
    user.email_verification_token = verification_token
    db.commit()

    await send_verification_email(email, verification_token)


async def update_user_profile(db: Session, user: User, name: Optional[str]) -> User:
    if name is not None:
        user.name = name
    db.commit()
    db.refresh(user)
    return user


async def change_user_password(
    db: Session, user: User, current_password: str, new_password: str
) -> None:
    if not user.password_hash or not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    user.password_hash = hash_password(new_password)
    db.commit()


async def set_user_password(db: Session, user: User, new_password: str) -> None:
    if user.password_hash is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password already set. Use change password instead.",
        )
    user.password_hash = hash_password(new_password)
    db.commit()


async def delete_user_account(db: Session, user: User) -> None:
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot be deleted.",
        )
    db.delete(user)
    db.commit()

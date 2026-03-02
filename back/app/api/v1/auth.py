from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    MessageResponse,
    RegistrationStatusResponse,
    ResetPasswordRequest,
    SetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserCreate,
    UserResponse,
)
from app.services.auth import (
    authenticate_google,
    authenticate_user,
    change_user_password,
    delete_user_account,
    register_user,
    request_password_reset,
    resend_verification_email,
    reset_password,
    set_user_password,
    update_user_profile,
    verify_email,
)
from app.utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/registration-status", response_model=RegistrationStatusResponse)
async def registration_status() -> RegistrationStatusResponse:
    return RegistrationStatusResponse(registration_enabled=settings.registration_enabled)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DbSession) -> User:
    if not settings.registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently closed",
        )
    return await register_user(db=db, email=data.email, password=data.password, name=data.name)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenResponse:
    user = await authenticate_user(db=db, email=form_data.username, password=form_data.password)
    access_token = create_access_token(str(user.id), is_admin=user.is_admin)
    return TokenResponse(access_token=access_token)


@router.post("/google", response_model=TokenResponse)
async def google_auth(data: GoogleAuthRequest, db: DbSession) -> TokenResponse:
    user = await authenticate_google(db=db, google_token=data.token)
    access_token = create_access_token(str(user.id), is_admin=user.is_admin)
    return TokenResponse(access_token=access_token)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: DbSession) -> MessageResponse:
    await request_password_reset(db=db, email=data.email)
    return MessageResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_route(data: ResetPasswordRequest, db: DbSession) -> MessageResponse:
    await reset_password(db=db, token=data.token, new_password=data.password)
    return MessageResponse(message="Password has been reset successfully.")


@router.get("/verify-email/{token}", response_model=MessageResponse)
async def verify_email_route(token: str, db: DbSession) -> MessageResponse:
    await verify_email(db=db, token=token)
    return MessageResponse(message="Email verified successfully.")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(data: ForgotPasswordRequest, db: DbSession) -> MessageResponse:
    await resend_verification_email(db=db, email=data.email)
    return MessageResponse(message="Verification email has been sent.")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> User:
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UpdateProfileRequest, current_user: CurrentUser, db: DbSession
) -> User:
    return await update_user_profile(db=db, user=current_user, name=data.name)


@router.put("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest, current_user: CurrentUser, db: DbSession
) -> MessageResponse:
    await change_user_password(
        db=db,
        user=current_user,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return MessageResponse(message="Password changed successfully.")


@router.put("/set-password", response_model=MessageResponse)
async def set_password(
    data: SetPasswordRequest, current_user: CurrentUser, db: DbSession
) -> MessageResponse:
    await set_user_password(db=db, user=current_user, new_password=data.new_password)
    return MessageResponse(message="Password set successfully.")


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(current_user: CurrentUser, db: DbSession) -> None:
    await delete_user_account(db=db, user=current_user)

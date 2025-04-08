from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
# Remove Session import if not used directly
# from sqlalchemy.orm import Session

# Relative imports - remove crud and models, keep schemas
# from app import crud, models, schemas
from .... import schemas # 4 dots to reach app level
# from app.api import deps # Assuming deps is no longer needed with direct service injection
# from app.core import security # Security functions likely moved to AuthService
from ....core.config import settings # 4 dots to reach app/core
from ....services.user_service import UserService # 4 dots to reach app/services
from ....services.auth_service import AuthService # 4 dots to reach app/services
from ....schemas.api import APIResponse # 4 dots to reach app/schemas

router = APIRouter()

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    access_token = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.Token)
async def register(
    user_data: schemas.UserCreate,
    auth_service: AuthService = Depends(),
    user_service: UserService = Depends()
):
    """
    Register a new user and return an access token.
    """
    # Create the user
    user = await user_service.create_user(user_data)
    
    # Generate an access token
    access_token = await auth_service.create_access_token(user.id)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh-token", response_model=schemas.Token)
async def refresh_token(
    token: str,
    auth_service: AuthService = Depends()
):
    """
    Refresh an access token.
    """
    new_token = await auth_service.refresh_token(token)
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": new_token, "token_type": "bearer"}

@router.post("/reset-password")
async def reset_password(
    email: str,
    auth_service: AuthService = Depends()
):
    """
    Send a password reset email.
    """
    await auth_service.send_password_reset(email)
    return {"message": "Password reset email sent"}

@router.post("/change-password")
async def change_password(
    token: str,
    new_password: str,
    auth_service: AuthService = Depends()
):
    """
    Change password using a reset token.
    """
    success = await auth_service.change_password(token, new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    return {"message": "Password changed successfully"} 
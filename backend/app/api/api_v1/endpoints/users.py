from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer

from ....schemas.user import User, UserCreate, UserUpdate
from ....services.user_service import UserService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    user_service: UserService = Depends()
):
    """
    Get all users (admin only).
    """
    return await user_service.get_users(skip=skip, limit=limit)

@router.get("/me", response_model=User)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Get the current authenticated user.
    """
    user = await user_service.get_current_user(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    user_service: UserService = Depends()
):
    """
    Get a specific user by ID.
    """
    user = await user_service.get_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends()
):
    """
    Create a new user.
    """
    return await user_service.create_user(user_data)

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Update a user.
    """
    # Check if the user is updating their own profile or is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_user = await user_service.update_user(user_id, user_data)
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Delete a user (admin only).
    """
    # Check if the user is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    deleted = await user_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return None 
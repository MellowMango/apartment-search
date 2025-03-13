from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer

from app.schemas.subscription import Subscription, SubscriptionCreate, SubscriptionUpdate
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/", response_model=List[Subscription])
async def get_subscriptions(
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(oauth2_scheme),
    subscription_service: SubscriptionService = Depends(),
    user_service: UserService = Depends()
):
    """
    Get all subscriptions (admin only).
    """
    # Check if the user is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await subscription_service.get_subscriptions(skip=skip, limit=limit)

@router.get("/me", response_model=Subscription)
async def get_my_subscription(
    token: str = Depends(oauth2_scheme),
    subscription_service: SubscriptionService = Depends(),
    user_service: UserService = Depends()
):
    """
    Get the current user's subscription.
    """
    current_user = await user_service.get_current_user(token)
    subscription = await subscription_service.get_user_subscription(current_user.id)
    
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return subscription

@router.get("/{subscription_id}", response_model=Subscription)
async def get_subscription(
    subscription_id: str,
    token: str = Depends(oauth2_scheme),
    subscription_service: SubscriptionService = Depends(),
    user_service: UserService = Depends()
):
    """
    Get a specific subscription by ID.
    """
    # Check if the user is an admin or the owner of the subscription
    current_user = await user_service.get_current_user(token)
    subscription = await subscription_service.get_subscription(subscription_id)
    
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    if current_user.id != subscription.user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return subscription

@router.post("/", response_model=Subscription, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    token: str = Depends(oauth2_scheme),
    subscription_service: SubscriptionService = Depends(),
    user_service: UserService = Depends()
):
    """
    Create a new subscription.
    """
    # Check if the user is an admin or creating a subscription for themselves
    current_user = await user_service.get_current_user(token)
    if current_user.id != subscription_data.user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await subscription_service.create_subscription(subscription_data)

@router.put("/{subscription_id}", response_model=Subscription)
async def update_subscription(
    subscription_id: str,
    subscription_data: SubscriptionUpdate,
    token: str = Depends(oauth2_scheme),
    subscription_service: SubscriptionService = Depends(),
    user_service: UserService = Depends()
):
    """
    Update a subscription.
    """
    # Check if the user is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_subscription = await subscription_service.update_subscription(subscription_id, subscription_data)
    if updated_subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return updated_subscription

@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: str,
    token: str = Depends(oauth2_scheme),
    subscription_service: SubscriptionService = Depends(),
    user_service: UserService = Depends()
):
    """
    Delete a subscription (admin only).
    """
    # Check if the user is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    deleted = await subscription_service.delete_subscription(subscription_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return None 
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError

# Relative imports
from ..core.config import settings
from ..schemas.user import User # Import User schema
from ..schemas.token import TokenPayload
# Remove SessionLocal and Base imports if not used for SQLAlchemy User lookup
# from app.db.session import SessionLocal
# from app.db.base_class import Base # Base is likely not needed

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/access-token"
)

# Remove get_db if SessionLocal is removed
# def get_db() -> Generator:
#     try:
#         db = SessionLocal()
#         yield db
#     finally:
#         db.close()

# Modify get_current_user to use Supabase or appropriate service
async def get_current_user(
    # Remove db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> Optional[User]: # Change type hint to schemas.User
    try:
        payload = jwt.decode(
            token, settings.AUTH_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    # TODO: Replace this with actual user lookup from Supabase/UserService
    # This is a placeholder assuming token_data.sub contains the user ID
    user_id = token_data.sub 
    if not user_id:
         raise HTTPException(status_code=404, detail="User not found in token")
         
    # Import and use UserService to get the user
    # This assumes UserService exists and has a method like get_user_by_id
    from ..services.user_service import UserService # Import here to avoid circular deps
    user_service = UserService() # Instantiate (or use Depends if refactored)
    user = await user_service.get_user(user_id=user_id) # Fetch user
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    # This part assumes the fetched User schema has an is_active attribute
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    # For now, just return the user as fetched by get_current_user
    return current_user

def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user 
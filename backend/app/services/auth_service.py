from typing import Optional
import jwt
from datetime import datetime, timedelta

# Relative imports
from ..core.config import settings
from ..db.supabase_client import get_supabase_client

class AuthService:
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """
        Authenticate a user and return an access token.
        """
        try:
            # Sign in with Supabase
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Get the user ID
            user_id = response.user.id
            
            # Create and return an access token
            return await self.create_access_token(user_id)
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None
    
    async def create_access_token(self, user_id: str) -> str:
        """
        Create an access token for a user.
        """
        # Set the expiration time
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        # Create the JWT payload
        to_encode = {
            "sub": user_id,
            "exp": expire
        }
        
        # Encode the JWT
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        return encoded_jwt
    
    async def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh an access token.
        """
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            
            if user_id is None:
                return None
            
            # Create a new access token
            return await self.create_access_token(user_id)
        except jwt.PyJWTError:
            return None
    
    async def send_password_reset(self, email: str) -> None:
        """
        Send a password reset email.
        """
        try:
            # Use Supabase's built-in password reset functionality
            self.supabase.auth.reset_password_email(email)
        except Exception as e:
            print(f"Password reset error: {str(e)}")
    
    async def change_password(self, token: str, new_password: str) -> bool:
        """
        Change password using a reset token.
        """
        try:
            # Use Supabase's built-in password update functionality
            self.supabase.auth.update_user({
                "password": new_password
            })
            return True
        except Exception as e:
            print(f"Password change error: {str(e)}")
            return False 
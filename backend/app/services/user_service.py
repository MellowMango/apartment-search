from typing import List, Optional, Dict, Any
import jwt
from datetime import datetime, timedelta

from app.core.config import settings
from app.schemas.user import UserCreate, UserUpdate, User
from app.db.supabase import get_supabase_client

class UserService:
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Get all users.
        """
        response = self.supabase.table("user_profiles").select("*").range(skip, skip + limit - 1).execute()
        
        # Convert to User objects
        users = []
        for item in response.data:
            # Get the auth user data
            auth_user = self.supabase.auth.admin.get_user_by_id(item["id"])
            
            # Combine auth user data with profile data
            user_data = {
                "id": item["id"],
                "email": auth_user.user.email,
                "full_name": item["full_name"],
                "company": item["company"],
                "job_title": item["job_title"],
                "phone": item["phone"],
                "avatar_url": item["avatar_url"],
                "subscription_tier": item["subscription_tier"],
                "subscription_status": item["subscription_status"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"]
            }
            
            users.append(User(**user_data))
        
        return users
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a specific user by ID.
        """
        response = self.supabase.table("user_profiles").select("*").eq("id", user_id).execute()
        
        if not response.data:
            return None
        
        # Get the auth user data
        auth_user = self.supabase.auth.admin.get_user_by_id(user_id)
        
        # Combine auth user data with profile data
        user_data = {
            "id": response.data[0]["id"],
            "email": auth_user.user.email,
            "full_name": response.data[0]["full_name"],
            "company": response.data[0]["company"],
            "job_title": response.data[0]["job_title"],
            "phone": response.data[0]["phone"],
            "avatar_url": response.data[0]["avatar_url"],
            "subscription_tier": response.data[0]["subscription_tier"],
            "subscription_status": response.data[0]["subscription_status"],
            "created_at": response.data[0]["created_at"],
            "updated_at": response.data[0]["updated_at"]
        }
        
        return User(**user_data)
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get the current authenticated user from the JWT token.
        """
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            
            if user_id is None:
                return None
            
            # Get the user from the database
            return await self.get_user(user_id)
        except jwt.PyJWTError:
            return None
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        """
        # Create the auth user
        auth_response = self.supabase.auth.admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True
        })
        
        # Create the user profile
        profile_data = {
            "id": auth_response.user.id,
            "full_name": user_data.full_name,
            "company": user_data.company,
            "job_title": user_data.job_title,
            "phone": user_data.phone,
            "avatar_url": user_data.avatar_url,
            "subscription_tier": "free",
            "subscription_status": "active"
        }
        
        response = self.supabase.table("user_profiles").insert(profile_data).execute()
        
        # Combine auth user data with profile data
        user_data = {
            "id": auth_response.user.id,
            "email": auth_response.user.email,
            "full_name": profile_data["full_name"],
            "company": profile_data["company"],
            "job_title": profile_data["job_title"],
            "phone": profile_data["phone"],
            "avatar_url": profile_data["avatar_url"],
            "subscription_tier": profile_data["subscription_tier"],
            "subscription_status": profile_data["subscription_status"],
            "created_at": response.data[0]["created_at"],
            "updated_at": response.data[0]["updated_at"]
        }
        
        return User(**user_data)
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """
        Update a user.
        """
        # Check if the user exists
        user = await self.get_user(user_id)
        if user is None:
            return None
        
        # Update the auth user if email is provided
        if user_data.email:
            self.supabase.auth.admin.update_user_by_id(user_id, {
                "email": user_data.email
            })
        
        # Update the user profile
        profile_data = {}
        if user_data.full_name:
            profile_data["full_name"] = user_data.full_name
        if user_data.company:
            profile_data["company"] = user_data.company
        if user_data.job_title:
            profile_data["job_title"] = user_data.job_title
        if user_data.phone:
            profile_data["phone"] = user_data.phone
        if user_data.avatar_url:
            profile_data["avatar_url"] = user_data.avatar_url
        
        if profile_data:
            response = self.supabase.table("user_profiles").update(profile_data).eq("id", user_id).execute()
        
        # Get the updated user
        return await self.get_user(user_id)
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        """
        # Check if the user exists
        user = await self.get_user(user_id)
        if user is None:
            return False
        
        # Delete the auth user
        self.supabase.auth.admin.delete_user(user_id)
        
        # The user_profiles record will be deleted automatically by the trigger
        
        return True 
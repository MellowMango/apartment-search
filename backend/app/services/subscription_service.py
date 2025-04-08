from typing import List, Optional, Dict, Any
from datetime import datetime

# Relative imports
from ..schemas.subscription import SubscriptionCreate, SubscriptionUpdate, Subscription
from ..db.supabase_client import get_supabase_client

class SubscriptionService:
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def get_subscriptions(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Subscription]:
        """
        Get all subscriptions.
        """
        response = self.supabase.table("subscriptions").select("*").range(skip, skip + limit - 1).execute()
        
        # Convert to Subscription objects
        subscriptions = [Subscription(**item) for item in response.data]
        
        return subscriptions
    
    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """
        Get a specific subscription by ID.
        """
        response = self.supabase.table("subscriptions").select("*").eq("id", subscription_id).execute()
        
        if not response.data:
            return None
        
        return Subscription(**response.data[0])
    
    async def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """
        Get a user's subscription.
        """
        response = self.supabase.table("subscriptions").select("*").eq("user_id", user_id).execute()
        
        if not response.data:
            return None
        
        return Subscription(**response.data[0])
    
    async def create_subscription(self, subscription_data: SubscriptionCreate) -> Subscription:
        """
        Create a new subscription.
        """
        # Check if the user already has a subscription
        existing_subscription = await self.get_user_subscription(subscription_data.user_id)
        if existing_subscription:
            # Update the existing subscription instead of creating a new one
            return await self.update_subscription(existing_subscription.id, SubscriptionUpdate(**subscription_data.dict()))
        
        # Create the subscription
        subscription_dict = subscription_data.dict()
        
        response = self.supabase.table("subscriptions").insert(subscription_dict).execute()
        
        # Update the user's subscription tier and status
        self.supabase.table("user_profiles").update({
            "subscription_tier": subscription_data.tier,
            "subscription_status": subscription_data.status
        }).eq("id", subscription_data.user_id).execute()
        
        return Subscription(**response.data[0])
    
    async def update_subscription(self, subscription_id: str, subscription_data: SubscriptionUpdate) -> Optional[Subscription]:
        """
        Update a subscription.
        """
        # Check if the subscription exists
        subscription = await self.get_subscription(subscription_id)
        if subscription is None:
            return None
        
        # Update the subscription
        subscription_dict = subscription_data.dict(exclude_unset=True)
        
        response = self.supabase.table("subscriptions").update(subscription_dict).eq("id", subscription_id).execute()
        
        if not response.data:
            return None
        
        # Update the user's subscription tier and status if provided
        update_data = {}
        if subscription_data.tier:
            update_data["subscription_tier"] = subscription_data.tier
        if subscription_data.status:
            update_data["subscription_status"] = subscription_data.status
        
        if update_data:
            self.supabase.table("user_profiles").update(update_data).eq("id", subscription.user_id).execute()
        
        return Subscription(**response.data[0])
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """
        Delete a subscription.
        """
        # Check if the subscription exists
        subscription = await self.get_subscription(subscription_id)
        if subscription is None:
            return False
        
        # Delete the subscription
        response = self.supabase.table("subscriptions").delete().eq("id", subscription_id).execute()
        
        # Update the user's subscription tier and status
        self.supabase.table("user_profiles").update({
            "subscription_tier": "free",
            "subscription_status": "inactive"
        }).eq("id", subscription.user_id).execute()
        
        return True 
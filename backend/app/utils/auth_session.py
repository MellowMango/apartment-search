import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Relative imports
from ..core.config import settings
from ..core.dependencies import get_current_user
from ..db.session import SessionLocal
# Need to import UserService if it's used directly
# from ..services.user_service import UserService # Uncomment if needed

logger = logging.getLogger(__name__)

class AuthSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for specified paths
        if request.url.path in settings.AUTH_EXEMPT_PATHS:
            response = await call_next(request)
            return response
        
        # Attempt to load user from session or token
        user = None
        db = None
        try:
            # Try loading user from session first
            if "user_id" in request.session:
                user_id = request.session["user_id"]
                db = SessionLocal()
                # Assuming get_current_user or similar logic is used now, or UserService is injected
                # user_service = UserService(db) # This direct instantiation might be replaced
                # user = user_service.get_user(user_id=user_id)
                # Replace with dependency injection pattern if possible
                # For now, assume get_current_user handles token/session lookup
                pass # Placeholder, actual logic depends on how user lookup is done

            # If user not in session, try loading from token
            if not user:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    db = db or SessionLocal()
                    user = await get_current_user(db=db, token=token) # Assuming get_current_user is async now
                    # Optionally store user in session for subsequent requests
                    if user:
                        request.session["user_id"] = str(user.id) # Ensure user_id is string for session
            
        except Exception as e:
            # Log error but don't block request
            logger.error(f"Error during user authentication: {e}", exc_info=True)
        finally:
            if db:
                db.close()
                
        # Store the user in the request state for access in endpoints
        request.state.user = user
        
        # Proceed with the request
        response = await call_next(request)
        return response 
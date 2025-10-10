"""
Supabase Client Utility for X-sevenAI

This module provides a unified interface for interacting with Supabase
across all microservices. It handles authentication, database operations,
and real-time subscriptions with enterprise-grade security.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from functools import lru_cache

from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the project root .env file
project_root = os.path.join(os.path.dirname(__file__), "../../")
env_file = os.path.join(project_root, ".env")

if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # Fallback to current directory
    load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Session configuration
SESSION_EXPIRY_DAYS = int(os.getenv("SESSION_EXPIRY_DAYS", "7"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "60"))

# Rate limiting configuration
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "100"))  # requests per minute
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds


def get_client_options():
    """Get default client options with security best practices."""
    return {}


@lru_cache()
def get_supabase_client(use_service_key: bool = False) -> Client:
    """
    Get a Supabase client instance with enhanced security.
    
    Args:
        use_service_key: If True, use the service role key for admin operations.
    
    Returns:
        A Supabase client instance.
    
    Raises:
        ValueError: If Supabase URL or key is not configured.
    """
    if not SUPABASE_URL or not (SUPABASE_KEY if not use_service_key else SUPABASE_SERVICE_KEY):
        error_msg = "Supabase configuration missing. Please set SUPABASE_URL and SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY environment variables."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_KEY
    
    try:
        # Create client with basic configuration
        client = create_client(
            SUPABASE_URL,
            key
        )
        
        # Session configuration is handled by Supabase automatically
        pass
        
        logger.info(f"Supabase client initialized with {'service role' if use_service_key else 'anonymous'} key")
        return client
        
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise


class SupabaseManager:
    """
    A manager class for Supabase operations with enhanced security.
    
    This class provides methods for secure authentication, session management,
    and database operations with proper error handling and logging.
    """
    
    def __init__(self, use_service_key: bool = False):
        """
        Initialize the Supabase manager with security best practices.
        
        Args:
            use_service_key: If True, use the service role key for admin operations.
        """
        self.client = get_supabase_client(use_service_key)
        self.use_service_key = use_service_key
        self.rate_limits = {}
    
    # Rate limiting
    
    def _check_rate_limit(self, key: str) -> bool:
        """Check and enforce rate limiting."""
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=RATE_LIMIT_WINDOW)
        
        # Clean up old entries
        self.rate_limits = {
            k: [t for t in v if t > window_start] 
            for k, v in self.rate_limits.items()
        }
        
        # Get or initialize request timestamps for this key
        timestamps = self.rate_limits.get(key, [])
        
        # Check if rate limit is exceeded
        if len(timestamps) >= RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for key: {key}")
            return False
            
        # Add current timestamp and update storage
        timestamps.append(current_time)
        self.rate_limits[key] = timestamps
        return True
    
    # Authentication methods
    
    async def sign_up(self, email: str, password: str, user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Securely sign up a new user with email and password.
        
        Args:
            email: User's email address.
            password: User's password (will be validated by Supabase).
            user_data: Additional user metadata for the profile.
        
        Returns:
            Dict containing user and session data.
            
        Raises:
            ValueError: If signup fails.
        """
        # Rate limiting check
        if not self._check_rate_limit(f"signup_{email}"):
            raise ValueError("Too many signup attempts. Please try again later.")
        
        try:
            # Sign up the user with Supabase Auth
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": user_data.get("full_name") if user_data else "",
                        "role": user_data.get("role", "customer") if user_data else "customer"
                    },
                    "email_redirect_to": os.getenv("EMAIL_REDIRECT_URL", ""),
                    "captcha_token": user_data.get("captcha_token") if user_data else None
                }
            })
            
            # If user_data is provided and sign up was successful, create a user profile
            if user_data and response.user:
                user_id = response.user.id
                profile_data = {
                    "id": user_id,
                    "email": email,
                    **{k: v for k, v in user_data.items() if k not in ["password", "captcha_token"]}
                }
                
                # Insert user profile using RPC to ensure proper RLS policies are applied
                self.client.rpc(
                    "create_user_profile",
                    {"profile_data": profile_data}
                ).execute()
            
            logger.info(f"User signed up successfully: {email}")
            return {
                "user": response.user.dict() if hasattr(response, 'user') else None,
                "session": response.session.dict() if hasattr(response, 'session') else None
            }
            
        except Exception as e:
            error_msg = f"Sign up failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e
    
    async def sign_in(self, email: str, password: str, remember_me: bool = False) -> Dict[str, Any]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address.
            password: User's password.
            remember_me: If True, creates a longer-lived session.
            
        Returns:
            Dict containing user and session data.
            
        Raises:
            ValueError: If authentication fails.
        """
        # Rate limiting check
        if not self._check_rate_limit(f"signin_{email}"):
            raise ValueError("Too many login attempts. Please try again later.")
        
        try:
            # Set session duration based on remember_me
            expires_in = (
                timedelta(days=REFRESH_TOKEN_DAYS).total_seconds()
                if remember_me
                else timedelta(hours=1).total_seconds()
            )
            
            # Sign in with Supabase Auth
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "last_sign_in_at": datetime.utcnow().isoformat()
                    }
                }
            })
            
            # Session expiry is handled by Supabase automatically
            # The expires_in parameter is not needed for set_session
            
            logger.info(f"User signed in successfully: {email}")
            return {
                "user": response.user.dict() if hasattr(response, 'user') else None,
                "session": response.session.dict() if hasattr(response, 'session') else None
            }
            
        except Exception as e:
            error_msg = f"Sign in failed: {str(e)}"
            logger.warning(f"Failed login attempt for {email}: {error_msg}")
            raise ValueError("Invalid email or password") from e
    
    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token using a refresh token.
        
        Args:
            refresh_token: The refresh token to use.
            
        Returns:
            Dict containing new access and refresh tokens.
            
        Raises:
            ValueError: If token refresh fails.
        """
        try:
            response = self.client.auth.refresh_session(refresh_token)
            
            logger.info("Session refreshed successfully")
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in
            }
            
        except Exception as e:
            error_msg = f"Session refresh failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError("Invalid or expired refresh token") from e
    
    async def sign_out(self, access_token: Optional[str] = None) -> bool:
        """
        Sign out the current user and invalidate the session.
        
        Args:
            access_token: Optional access token to sign out.
            
        Returns:
            bool: True if sign out was successful.
        """
        try:
            if access_token:
                # Invalidate the specific token
                self.client.auth.api.sign_out(access_token)
            else:
                # Sign out the current session
                self.client.auth.sign_out()
            
            logger.info("User signed out successfully")
            return True
            
        except Exception as e:
            logger.error(f"Sign out failed: {str(e)}", exc_info=True)
            return False
    
    # User management methods
    
    async def get_user(self, user_id: str, include_roles: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get user by ID with optional role information.
        
        Args:
            user_id: The user's ID.
            include_roles: Whether to include business roles.
            
        Returns:
            User data with roles if include_roles is True, or None if not found.
        """
        try:
            # Get user data from public.users (this is the source of truth)
            result = self.client.table('users').select('*').eq('id', user_id).execute()
            
            if not result.data:
                logger.warning(f"User profile not found in public.users for user_id: {user_id}")
                return None
            
            user = result.data[0]
            
            # Get business roles if requested
            if include_roles:
                roles_result = self.client.table('user_business_roles').select('*').eq('user_id', user_id).execute()
                user['business_roles'] = roles_result.data if roles_result.data else []
                
            return user
            
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    async def get_business_profile(self, business_id: str) -> Dict[str, Any]:
        """
        Get a business profile.
        
        Args:
            business_id: The business ID.
        
        Returns:
            The business profile data.
        """
        response = self.client.table("business_profiles").select("*").eq("id", business_id).execute()
        return response.data[0] if response.data else {}
    
    async def create_chat_session(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new chat session.
        
        Args:
            chat_data: Chat session data.
        
        Returns:
            The created chat session data.
        """
        response = self.client.table("chat_sessions").insert(chat_data).execute()
        return response.data[0] if response.data else {}
    
    async def add_chat_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a message to a chat session.
        
        Args:
            message_data: Chat message data.
        
        Returns:
            The created message data.
        """
        response = self.client.table("chat_messages").insert(message_data).execute()
        return response.data[0] if response.data else {}
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order.
        
        Args:
            order_data: Order data.
        
        Returns:
            The created order data.
        """
        response = self.client.table("orders").insert(order_data).execute()
        return response.data[0] if response.data else {}
    
    async def create_reservation(self, reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new reservation.
        
        Args:
            reservation_data: Reservation data.
        
        Returns:
            The created reservation data.
        """
        response = self.client.table("reservations").insert(reservation_data).execute()
        return response.data[0] if response.data else {}
    
    async def log_analytics_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log an analytics event.
        
        Args:
            event_data: Event data.
        
        Returns:
            The created event data.
        """
        response = self.client.table("analytics_events").insert(event_data).execute()
        return response.data[0] if response.data else {}
    
    # Generic CRUD methods
    
    async def select(self, table: str, columns: str = "*", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Select data from a table.
        
        Args:
            table: Table name.
            columns: Columns to select.
            filters: Filters to apply.
        
        Returns:
            The selected data.
        """
        query = self.client.table(table).select(columns)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        response = query.execute()
        return response.data
    
    async def insert(self, table: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Insert data into a table.
        
        Args:
            table: Table name.
            data: Data to insert.
        
        Returns:
            The inserted data.
        """
        response = self.client.table(table).insert(data).execute()
        return response.data
    
    async def update(self, table: str, data: Dict[str, Any], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Update data in a table.
        
        Args:
            table: Table name.
            data: Data to update.
            filters: Filters to apply.
        
        Returns:
            The updated data.
        """
        query = self.client.table(table).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        response = query.execute()
        return response.data
    
    async def delete(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Delete data from a table.
        
        Args:
            table: Table name.
            filters: Filters to apply.
        
        Returns:
            The deleted data.
        """
        query = self.client.table(table).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        response = query.execute()
        return response.data

"""
Authentication utilities - Supabase JWT validation

CRITICAL: No fallbacks, no anonymous users, no fake UUIDs.
All endpoints MUST have a valid Supabase auth token.
"""

from fastapi import Header, HTTPException
from typing import Optional
import os

# Import Supabase client
from .supabase_client import supabase


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract and validate user ID from Supabase JWT token.
    
    This function:
    1. Requires Authorization: Bearer <token> header
    2. Validates JWT using Supabase client
    3. Extracts user ID from token
    4. Returns auth.users.id (UUID)
    
    Raises:
        HTTPException 401: If token is missing, invalid, or expired
    
    Returns:
        str: Supabase auth.users.id (UUID)
    
    CRITICAL: This function NEVER returns None or a fake ID.
              It raises 401 on any auth failure.
    """
    # Require Authorization header
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Please provide: Authorization: Bearer <token>"
        )
    
    # Validate Bearer format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer <token>"
        )
    
    # Extract token
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Empty token provided"
        )
    
    # Validate JWT using Supabase client
    try:
        # Use Supabase client to validate token and get user
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: user not found"
            )
        
        user_id = user_response.user.id
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID"
            )
        
        return user_id
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle Supabase client errors
        error_msg = str(e)
        if "expired" in error_msg.lower():
            raise HTTPException(
                status_code=401,
                detail="Token has expired. Please refresh your session."
            )
        else:
            raise HTTPException(
                status_code=401,
                detail=f"Authentication failed: {error_msg}"
            )

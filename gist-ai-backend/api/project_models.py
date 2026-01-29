"""
Project-related Pydantic models
"""

from pydantic import BaseModel
from typing import Optional, List

class ProjectCreate(BaseModel):
    """Request model for creating a project"""
    title: str


class ProjectResponse(BaseModel):
    """Response model for a project"""
    id: str
    title: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: str
    created_at: str
    updated_at: str


class ProjectListResponse(BaseModel):
    """Response model for list of projects"""
    projects: List[ProjectResponse]

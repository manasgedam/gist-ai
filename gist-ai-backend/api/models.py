"""
Database models and Pydantic schemas
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import datetime

Base = declarative_base()

class ProcessingStage:
    PENDING = "pending"
    INGESTING = "ingesting"
    TRANSCRIBING = "transcribing"
    UNDERSTANDING = "understanding"
    GROUPING = "grouping"
    RANKING = "ranking"
    COMPLETE = "complete"
    FAILED = "failed"


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    youtube_url = Column(String, nullable=False)
    youtube_id = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds
    thumbnail = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)
    transcript_path = Column(String, nullable=True)
    
    status = Column(String, default=ProcessingStage.PENDING)
    current_stage = Column(String, default=ProcessingStage.PENDING)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(String, default=lambda: datetime.datetime.now().isoformat())
    updated_at = Column(String, default=lambda: datetime.datetime.now().isoformat())

    # Relationships
    ideas = relationship("Idea", back_populates="video", cascade="all, delete-orphan")


class Idea(Base):
    __tablename__ = "ideas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    strength = Column(String, nullable=True)
    viral_potential = Column(Float, nullable=True)
    
    # JSON fields for structured data
    highlights = Column(JSON, nullable=True)
    time_ranges = Column(JSON, nullable=True)  # List of {start, end}
    
    created_at = Column(String, default=lambda: datetime.datetime.now().isoformat())

    # Relationships
    video = relationship("Video", back_populates="ideas")


# ============================================================================
# Pydantic Models
# ============================================================================

class VideoSubmitRequest(BaseModel):
    url: str
    project_id: Optional[str] = None
    mode: Optional[str] = "auto"


class VideoResponse(BaseModel):
    video_id: str
    status: str
    message: str


class VideoStatusResponse(BaseModel):
    video_id: str
    status: str
    progress: int
    current_stage: Optional[str]
    message: str


class TimeRangeSchema(BaseModel):
    start: float
    end: float


class IdeaResponse(BaseModel):
    id: str
    rank: int
    title: str
    description: Optional[str]
    strength: Optional[str]
    viral_potential: Optional[float]
    highlights: Optional[List[str]] = []
    time_ranges: List[TimeRangeSchema]


class IdeasResponse(BaseModel):
    video_id: str
    ideas: List[IdeaResponse]


class TimelineSegment(BaseModel):
    start: float
    end: float
    label: str
    ideas: List[str]  # Idea IDs


class TimelineResponse(BaseModel):
    video_id: str
    video_url: str
    duration: float
    title: str
    thumbnail: Optional[str]
    segments: List[TimelineSegment]

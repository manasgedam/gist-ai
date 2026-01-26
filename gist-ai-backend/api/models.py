from enum import Enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel
import uuid

Base = declarative_base()


class ProcessingStage(str, Enum):
    """Processing pipeline stages"""
    PENDING = "PENDING"
    INGESTING = "INGESTING"
    TRANSCRIBING = "TRANSCRIBING"
    UNDERSTANDING = "UNDERSTANDING"
    GROUPING = "GROUPING"
    RANKING = "RANKING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class Video(Base):
    """Video database model"""
    __tablename__ = "videos"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    youtube_url = Column(String, nullable=False)
    youtube_id = Column(String, nullable=True)
    title = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    status = Column(SQLEnum(ProcessingStage), default=ProcessingStage.PENDING)
    current_stage = Column(SQLEnum(ProcessingStage), default=ProcessingStage.PENDING)
    progress = Column(Integer, default=0)
    video_path = Column(String, nullable=True)
    transcript_path = Column(String, nullable=True)
    ideas_path = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    ideas = relationship("Idea", back_populates="video", cascade="all, delete-orphan")


class Idea(Base):
    """Idea database model"""
    __tablename__ = "ideas"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    strength = Column(String, nullable=False)  # "high" | "medium" | "low"
    viral_potential = Column(String, nullable=True)
    highlights = Column(JSON, nullable=True)  # Array of strings
    time_ranges = Column(JSON, nullable=False)  # Array of TimeRange objects
    
    # Relationship
    video = relationship("Video", back_populates="ideas")


# Pydantic Schemas for API

class TimeRangeSchema(BaseModel):
    """Time range schema"""
    start: float
    end: float
    confidence: float = 1.0


class VideoSubmitRequest(BaseModel):
    """Request schema for submitting a YouTube URL"""
    url: str
    mode: str = "groq"


class VideoResponse(BaseModel):
    """Response schema for video submission"""
    video_id: str
    status: ProcessingStage
    message: str


class VideoStatusResponse(BaseModel):
    """Response schema for video status"""
    video_id: str
    status: ProcessingStage
    progress: int
    current_stage: ProcessingStage
    message: str
    estimated_completion: Optional[str] = None


class IdeaResponse(BaseModel):
    """Response schema for an idea"""
    id: str
    rank: int
    title: str
    reason: str
    strength: str
    viral_potential: Optional[str]
    highlights: List[str]
    time_ranges: List[TimeRangeSchema]


class IdeasResponse(BaseModel):
    """Response schema for all ideas"""
    video_id: str
    ideas: List[IdeaResponse]


class TimelineSegment(BaseModel):
    """Timeline segment schema"""
    start: float
    end: float
    label: str
    ideas: List[str]  # List of idea IDs


class TimelineResponse(BaseModel):
    """Response schema for timeline"""
    video_id: str
    video_url: str
    duration: float
    title: str
    thumbnail: Optional[str]
    segments: List[TimelineSegment]


class WebSocketMessage(BaseModel):
    """WebSocket message schema"""
    type: str  # "progress" | "stage_complete" | "complete" | "error"
    stage: Optional[ProcessingStage] = None
    progress: Optional[int] = None
    message: Optional[str] = None
    next_stage: Optional[ProcessingStage] = None
    ideas_count: Optional[int] = None
    error: Optional[str] = None
    timestamp: str = datetime.utcnow().isoformat()

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True) # UUID for the job
    url = Column(String, nullable=True)
    title = Column(String)
    status = Column(String, default="PENDING") # PENDING, TRANSCRIBING, COMPLETED
    local_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships: One video can have many transcript segments and many AI clips
    transcripts = relationship("Transcript", back_populates="video", cascade="all, delete-orphan")
    clips = relationship("Clip", back_populates="video", cascade="all, delete-orphan")

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True)
    video_id = Column(String, ForeignKey("videos.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    content = Column(Text)

    video = relationship("Video", back_populates="transcripts")

class Clip(Base):
    __tablename__ = "clips"

    id = Column(Integer, primary_key=True)
    video_id = Column(String, ForeignKey("videos.id"))
    title = Column(String)
    start_time = Column(Float)
    end_time = Column(Float)
    hook_reason = Column(Text)

    video = relationship("Video", back_populates="clips")
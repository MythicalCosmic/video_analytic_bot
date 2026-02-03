from sqlalchemy import Column, String, Integer, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database.models.base import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(String(36), primary_key=True)  
    creator_id = Column(String(32), nullable=False, index=True)  
    video_created_at = Column(DateTime(timezone=True), nullable=False)
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    reports_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to snapshots
    snapshots = relationship("VideoSnapshot", back_populates="video", lazy="selectin")

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_videos_video_created_at', 'video_created_at'),
        Index('idx_videos_views_count', 'views_count'),
        Index('idx_videos_creator_video_date', 'creator_id', 'video_created_at'),
    )

    def __repr__(self):
        return f"<Video(id={self.id}, views={self.views_count})>"
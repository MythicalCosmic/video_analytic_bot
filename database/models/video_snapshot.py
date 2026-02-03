from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database.models.base import Base


class VideoSnapshot(Base):
    __tablename__ = "video_snapshots"

    id = Column(String(32), primary_key=True) 
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    reports_count = Column(Integer, default=0)
    
    delta_views_count = Column(Integer, default=0)
    delta_likes_count = Column(Integer, default=0)
    delta_comments_count = Column(Integer, default=0)
    delta_reports_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    video = relationship("Video", back_populates="snapshots")

    __table_args__ = (
        Index('idx_snapshots_video_id', 'video_id'),
        Index('idx_snapshots_created_at', 'created_at'),
        Index('idx_snapshots_video_created', 'video_id', 'created_at'),
        Index('idx_snapshots_delta_views_positive', 'delta_views_count', 
              postgresql_where='delta_views_count > 0'),
    )

    def __repr__(self):
        return f"<VideoSnapshot(id={self.id}, video_id={self.video_id}, delta_views={self.delta_views_count})>"
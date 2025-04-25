from sqlalchemy import Column, Integer, String, DateTime, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("title", "organizer", "event_link", name="uix_event_identity"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    title = Column(String, index=True)
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    organizer = Column(String, index=True)
    industry = Column(String, index=True)
    market = Column(String, index=True)
    attending = Column(String, index=True)
    event_link = Column(String, index=True)
    color = Column(String, index=True)
    note = Column(String)
    valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

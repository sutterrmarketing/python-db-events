from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    title = Column(String, index=True)
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    organizer = Column(String, index=True)
    industry = Column(String)
    market = Column(String)
    attending = Column(String)
    event_link = Column(String, index=True)
    color = Column(String)
    note = Column(String)
    valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

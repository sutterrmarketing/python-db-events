from fastapi import Query
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class EventQueryParams(BaseModel):
    search: Optional[str] = None
    market: Optional[str] = None
    industry: Optional[str] = None
    sort: Optional[str] = "start_datetime"  # default sort
    order: Optional[str] = "asc"  # asc or desc
    start_after: Optional[datetime] = None
    start_before: Optional[datetime] = None
    valid: Optional[bool] = True
    limit: int = 100
    offset: int = 0


class EventResponse(BaseModel):
    id: int
    title: Optional[str]
    organizer: Optional[str]
    event_link: Optional[str]
    market: Optional[str]
    industry: Optional[str]
    attending: Optional[str]
    color: Optional[str]
    note: Optional[str]
    start_datetime: Optional[datetime]
    end_datetime: Optional[datetime]
    valid: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class EventCreate(BaseModel):
    title: str
    organizer: str
    event_link: str
    market: Optional[str] = None
    industry: Optional[str] = None
    attending: Optional[str] = None
    color: Optional[str] = None
    note: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    valid: Optional[bool] = True


class EventUpdate(BaseModel):
    title: Optional[str]
    event_link: Optional[str]
    organizer: Optional[str]
    market: Optional[str]
    industry: Optional[str]
    attending: Optional[str]
    color: Optional[str]
    note: Optional[str]
    start_datetime: Optional[datetime]
    end_datetime: Optional[datetime]
    valid: Optional[bool]

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

import importlib
from app.src.utils import deduplicate_events, load_config
from app.src.db.database import SessionLocal
from app.src.db.schemas import EventResponse, EventUpdate, EventCreate
from app.src.db.database import init_db
from app.src.db.models import Event

from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

init_db()

app = FastAPI()

class EventRequest(BaseModel):
    websites: List[str]

def parse_datetime(dt_input) -> datetime | None:
    if isinstance(dt_input, datetime):
        return dt_input
    if isinstance(dt_input, str) and dt_input.strip():
        try:
            return datetime.fromisoformat(dt_input)
        except Exception as ex:
            print(f"[WARNING] Failed to parse datetime string: '{dt_input}' — {ex}")
    return None


@app.post("/events", response_model=List[EventResponse])
async def fetch_events(request: EventRequest):
    all_events = []

    for site in request.websites:
        try:
            config = load_config(site)
            module = importlib.import_module(f"app.site.{site}")
            events_raw = module.process(config)
            events = deduplicate_events(events_raw)
            all_events.extend(events)
        except Exception as e:
            print(f"Error processing {site}: {e}")

    db: Session = SessionLocal()
    stored_events = []

    try:
        for e in all_events:
            title = e.get("Event Title")
            event_link = e.get("Event Link")
            organizer = e.get("Organizer")

            if not (title and event_link and organizer):
                continue  # skip incomplete

            existing = (
                db.query(Event)
                .filter_by(title=title, event_link=event_link, organizer=organizer)
                .first()
            )

            start_dt = parse_datetime(e.get("start_dt"))
            end_dt = parse_datetime(e.get("end_dt"))

            if existing:
                existing.start_datetime = start_dt
                existing.end_datetime = end_dt
                existing.updated_at = datetime.now()
                stored_events.append(existing)
            else:
                new_event = Event(
                    title=title,
                    event_link=event_link,
                    organizer=organizer,
                    industry=e.get("Industry"),
                    market=e.get("Market"),
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    valid=True,
                )
                db.add(new_event)
                stored_events.append(new_event)

        db.commit()

        for ev in stored_events:
            db.refresh(ev)

        return stored_events

    finally:
        db.close()


@app.get("/events", response_model=List[EventResponse])
def get_events(
    search: Optional[str] = Query(None),
    market: Optional[List[str]] = Query(None),
    industry: Optional[List[str]] = Query(None),
    organizer: Optional[List[str]] = Query(None),
    valid: Optional[bool] = Query(True),
    start_after: Optional[datetime] = Query(None),
    start_before: Optional[datetime] = Query(None),
    sort: Optional[str] = Query("start_datetime"),
    order: Optional[str] = Query("asc"),
    limit: int = Query(1000000),
    offset: int = Query(0),
):
    db: Session = SessionLocal()

    try:
        query = db.query(Event)

        if search:
            query = query.filter(Event.title.ilike(f"%{search}%"))

        if market:
            query = query.filter(Event.market.in_(market))

        if industry:
            query = query.filter(Event.industry.in_(industry))

        if organizer:
            query = query.filter(Event.organizer.in_(organizer))

        if start_after:
            query = query.filter(Event.start_datetime >= start_after)

        if start_before:
            query = query.filter(Event.start_datetime <= start_before)

        if valid is not None:
            query = query.filter(Event.valid == valid)

        # Sorting logic
        sort_column = getattr(Event, sort, Event.start_datetime)
        sort_func = asc if order == "asc" else desc
        query = query.order_by(sort_func(sort_column))

        events = query.offset(offset).limit(limit).all()
        return events

    finally:
        db.close()


@app.get("/events/{id}", response_model=EventResponse)
def get_event(id: int):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event
    finally:
        db.close()


@app.put("/events/{id}", response_model=EventResponse)
def update_event(id: int, update: EventUpdate):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(event, field, value)

        event.updated_at = datetime.now()
        db.commit()
        db.refresh(event)

        return event
    finally:
        db.close()


@app.delete("/events/{id}", response_model=EventResponse)
def delete_event(id: int):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        db.delete(event)
        db.commit()
        return event
    finally:
        db.close()


@app.post("/events/new", response_model=EventResponse)
def create_event(event: EventCreate):
    db = SessionLocal()
    try:
        new_event = Event(
            title=event.title,
            organizer=event.organizer,
            event_link=event.event_link,
            market=event.market,
            industry=event.industry,
            attending=event.attending,
            color=event.color,
            note=event.note,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            valid=event.valid if event.valid is not None else True,
        )

        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return new_event
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.src.api.events:app", host="0.0.0.0", port=8000, reload=True)

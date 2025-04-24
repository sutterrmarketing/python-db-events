import uvicorn
from app.src.api import events
from app.src.db.database import init_db

app = events.app

init_db()

if __name__ == "__main__":
    uvicorn.run("app.src.web:app", host="0.0.0.0", port=8000, reload=True)

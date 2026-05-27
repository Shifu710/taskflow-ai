from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.seed import seed_database
from app.db.session import Base, SessionLocal, engine
from app.models import entities  # noqa: F401

frontend_origins = [origin.strip() for origin in settings.frontend_origins.split(",") if origin.strip()]

app = FastAPI(title="TaskFlow AI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"ok": True}

from celery import Celery

from app.core.config import settings
from app.db.session import SessionLocal
from app.runtime.engine import execute_until_pause_or_done

celery_app = Celery(
    "taskflow_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


@celery_app.task(name="taskflow.run_workflow")
def run_workflow_task(run_id: str) -> dict:
    db = SessionLocal()
    try:
        run = execute_until_pause_or_done(db, run_id, approved=False)
        return {"run_id": run.id, "status": run.status}
    finally:
        db.close()

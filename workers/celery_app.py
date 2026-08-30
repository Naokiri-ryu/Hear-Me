from celery import Celery

from api.config import settings

celery_app = Celery(
    "hear_me",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "workers.tasks.ping",
        "workers.tasks.spotify",
        "workers.tasks.sort_playlist",
        "workers.tasks.enrich_playlist",
        "workers.tasks.group_playlist",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Idempotent, retried tasks with backoff per platform rate limits handled
    # inside task implementations (see AGENTS.md -> SKILL.md pattern).
)
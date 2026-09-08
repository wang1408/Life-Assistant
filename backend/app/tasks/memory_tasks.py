from app.core.celery_app import celery_app


@celery_app.task(name="app.tasks.memory_tasks.extract_memories")
def extract_memories(message: str) -> list[dict]:
    from app.agents.memory_agent import extract_candidates
    return extract_candidates(message)


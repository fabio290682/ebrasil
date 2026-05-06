"""
Async background scheduler for the RPA.

Runs as a long-lived asyncio task started in FastAPI's lifespan.
Every CHECK_INTERVAL_SECONDS it checks which fontes are overdue and runs them.
"""
from __future__ import annotations

import asyncio

import structlog

from ..database import SessionLocal

logger = structlog.get_logger()

CHECK_INTERVAL_SECONDS = 1800  # Check every 30 minutes

_task: asyncio.Task | None = None


async def _loop() -> None:
    logger.info("rpa_scheduler_started", interval_s=CHECK_INTERVAL_SECONDS)
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            await _run_pending()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("rpa_scheduler_error", error=str(exc))


async def _run_pending() -> None:
    from .runner import RpaRunner
    with SessionLocal() as db:
        runner = RpaRunner(db)
        ran = await runner.run_pending()
        if ran:
            logger.info("rpa_scheduler_ran", fontes=ran)


def start() -> None:
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_loop())
        logger.info("rpa_scheduler_task_created")


def stop() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
        logger.info("rpa_scheduler_stopped")

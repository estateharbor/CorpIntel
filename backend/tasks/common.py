"""Shared helpers for Celery tasks."""
from __future__ import annotations

import asyncio


def run_async(coro):
    """Run a coroutine from a synchronous Celery task body."""
    return asyncio.run(coro)

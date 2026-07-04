"""Shared helpers for Celery tasks."""
from __future__ import annotations

import asyncio


def run_async(coro):
    return asyncio.run(coro)

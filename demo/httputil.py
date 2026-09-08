"""Shared HTTP helper for FastAPI tests."""

from __future__ import annotations

import asyncio

import httpx


def asgi_request(app, method: str, path: str, **kwargs):
    async def _go():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_go())

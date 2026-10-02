"""Talking to the app as the table's browser does, without a browser."""

import httpx2
from fastapi import FastAPI


def client(app: FastAPI) -> httpx2.AsyncClient:
    return httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url="http://table")


def frames(body: str) -> list[dict[str, str]]:
    """Parse an SSE body into its frames, as an EventSource would see them."""
    parsed = []
    for block in body.strip().split("\n\n"):
        frame = {}
        for line in block.splitlines():
            if line.startswith(":"):
                continue
            name, _, value = line.partition(": ")
            frame[name] = value
        if frame:
            parsed.append(frame)
    return parsed

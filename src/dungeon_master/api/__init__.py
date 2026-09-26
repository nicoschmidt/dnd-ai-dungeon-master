"""The API layer: translates HTTP into calls on the session.

The only package that imports a web framework (`fastapi`, `starlette`,
`uvicorn`). It holds no game logic; route handlers stay thin.
"""

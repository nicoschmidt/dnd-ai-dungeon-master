"""The table's event contract: what the shared screen receives, and nothing else.

Pydantic models declared once here and mirrored in the client as generated
TypeScript types (ADR-0005, commitment 3). Imports neither a web framework nor
the Claude Agent SDK.
"""

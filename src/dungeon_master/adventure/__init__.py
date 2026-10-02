"""Adventure content, reached through a port and never through a path (ADR-0003).

The domain models of what an adventure contains, the `AdventureRepository`
port, and an in-memory implementation. Imports neither a web framework nor the
Claude Agent SDK. Real adventure content never lives here: only original or
SRD material, under `fixtures/`, with its provenance.
"""

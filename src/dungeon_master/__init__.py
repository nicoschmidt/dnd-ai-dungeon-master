"""An AI dungeon master for tabletop Dungeons & Dragons.

The package is layered as ADR-0005 commits it to be. FastAPI lives in `api`
and nowhere else; the Claude Agent SDK lives in `orchestration` and nowhere
else. `rules` and `session` import neither.
"""

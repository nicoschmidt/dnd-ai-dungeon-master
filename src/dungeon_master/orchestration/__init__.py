"""Session orchestration: runs the dungeon master agent.

The only package that imports the Claude Agent SDK (`claude_agent_sdk`). It
builds the agent's context, streams narration and exposes the tool surface.
It does not import a web framework.
"""

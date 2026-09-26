"""The tool layer: the only way durable state changes.

The contract between the agent and everything durable. Tools call into the
rules core and session state. Contracts are designed from the domain, not from
how the model happens to behave.
"""

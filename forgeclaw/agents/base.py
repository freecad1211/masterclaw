"""
Base classes and utilities for debates in the `forgeclaw.agents` package.

The base class centralises logging and the required interface for all debate
agents.  Concrete implementations should inherit from :class:`BaseDebateAgent`
and implement :py:meth:`propose`, :py:meth:`critique` and :py:meth:`decide`.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from forgeclaw.models.debate import AgentMessage, DebateRequest

logger = logging.getLogger(__name__)


class BaseDebateAgent(ABC):
    """Abstract base for all debate agents.

    Attributes
    ----------
    role: str
        Identifier of the agent role (e.g., ``"architect"``).
    """

    role: str

    def __init__(self, *_, **__):  # pragma: no cover - trivial
        super().__init__()

    @abstractmethod
    def propose(self, request: DebateRequest) -> AgentMessage:
        """Return the initial proposal for a debate request."""

    @abstractmethod
    def critique(self, request: DebateRequest, proposal: AgentMessage) -> AgentMessage:  # pragma: no cover - interface
        """Return a critique of the proposal."""

    @abstractmethod
    def decide(self, request: DebateRequest, proposal: AgentMessage, critique: AgentMessage) -> AgentMessage:  # pragma: no cover - interface
        """Return the final decision after receiving critique."""

    # Helper for consistent debug output
    def _log(self, msg: str) -> None:
        logger.debug(f"[{self.role}] {msg}")

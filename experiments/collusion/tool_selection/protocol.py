"""Protocol subclass. Canonicalizes tool identity only in prefetched observations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from experiments.common.local_protocol_tracebreak import LocalCommunicationProtocol
from experiments.collusion.tool_selection.observation import canonicalize_observation_text


class ToolSelectionProtocol(LocalCommunicationProtocol):
    def _canonicalize(self) -> bool:
        experiment = (self.config.get("experiment") or {})
        probe = experiment.get("tool_selection") or {}
        return bool(probe.get("canonicalize_identity"))

    async def _prefetch_blackboard_events(
        self,
        agent_name: str,
        *,
        phase: Optional[str],
        iteration: Optional[int],
    ) -> Dict[str, str]:
        contexts = await super()._prefetch_blackboard_events(
            agent_name,
            phase=phase,
            iteration=iteration,
        )
        if not self._canonicalize():
            return contexts
        return {
            key: canonicalize_observation_text(value)
            for key, value in contexts.items()
        }

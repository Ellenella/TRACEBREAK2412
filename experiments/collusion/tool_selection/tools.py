"""Two execution tools that claim a task through one shared implementation.

The callable names differ. The assignment, validation, and result payload do not.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

DIRECT = "assign_task_direct"
QUEUED = "assign_task_queued"
TOOL_NAMES = (DIRECT, QUEUED)


def _schema(name: str) -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": "Claim a task id from the public task list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task id from your task list.",
                    }
                },
                "required": ["task_id"],
            },
        },
    }


class JiraTicketToolSelectionTools:
    """Execution tools for the exploratory tool-identity study."""

    def __init__(self, blackboard_manager: Any):
        self.blackboard_manager = blackboard_manager

    def get_tool_names(self) -> Set[str]:
        return set(TOOL_NAMES)

    def get_tools(self, phase: str) -> List[Dict[str, Any]]:
        if phase != "execution":
            return []
        return [_schema(name) for name in TOOL_NAMES]

    def claim(
        self,
        tool_name: str,
        agent_name: str,
        task_id: str,
        *,
        phase: Optional[str],
        iteration: Optional[int],
        env_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        tasks = env_state.get("tasks", {})
        assignment = env_state.get("assignment", {})
        agent_names = env_state.get("agent_names", [])
        if agent_name not in agent_names:
            return {"status": "failed", "reason": f"Agent {agent_name} not found"}
        if agent_name in assignment:
            return {"status": "failed", "reason": f"Agent {agent_name} already assigned"}
        if task_id not in tasks:
            return {
                "status": "retry",
                "reason": f"Unknown task_id {task_id}",
                "suggestions": ["Choose a task_id from your TASKS list."],
            }
        updated = dict(assignment)
        updated[agent_name] = task_id
        result = {
            "agent": agent_name,
            "task_id": task_id,
            "task": tasks.get(task_id, {}),
            "total_assigned": len(updated),
            "remaining_agents": len(agent_names) - len(updated),
            "state_updates": {"assignment": {agent_name: task_id}},
        }
        execution_result = {"status": "success", "result": result}
        action = {"action": tool_name, "task_id": task_id}
        if self.blackboard_manager is not None:
            self.blackboard_manager.log_action_to_blackboards(
                agent_name, action, execution_result, phase, iteration
            )
        return execution_result

    def handle_tool_call(
        self,
        tool_name: str,
        agent_name: str,
        arguments: Dict[str, Any],
        phase: Optional[str] = None,
        iteration: Optional[int] = None,
        env_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if tool_name not in TOOL_NAMES:
            return {"error": f"Tool-selection environment does not support tool: {tool_name}"}
        task_id = arguments.get("task_id")
        if task_id is None:
            return {"error": "task_id is required"}
        return self.claim(
            tool_name,
            agent_name,
            str(task_id),
            phase=phase,
            iteration=iteration,
            env_state=env_state or {},
        )

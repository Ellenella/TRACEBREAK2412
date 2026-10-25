"""Jira environment that exposes the tool-selection toolset."""

from __future__ import annotations

from envs.dcops.jira_ticket.jira_ticket_env import JiraTicketEnvironment

from experiments.collusion.tool_selection.register import ENV_NAME


class JiraTicketToolSelectionEnvironment(JiraTicketEnvironment):
    tools_environment_name = ENV_NAME

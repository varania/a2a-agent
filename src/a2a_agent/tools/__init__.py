"""Tools the agent can call."""

from a2a_agent.tools.calculator import calculator
from a2a_agent.tools.clock import get_current_time

__all__ = ["TOOLS", "calculator", "get_current_time"]

TOOLS = [calculator, get_current_time]

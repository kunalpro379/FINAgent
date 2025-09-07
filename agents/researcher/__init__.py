"""
Research Agents

This module contains research agents that analyze market conditions:
- Bull Researcher: Optimistic market analysis
- Bear Researcher: Pessimistic market analysis
"""

from .bull import create_bull_researcher
from .bear import create_bear_researcher

__all__ = [
    'create_bull_researcher',
    'create_bear_researcher'
]

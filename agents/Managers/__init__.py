"""
Manager Agents

This module contains manager agents that coordinate and make decisions:
- Research Manager: Coordinates bull/bear research and makes investment decisions
- Risk Manager: Manages risk assessment and portfolio risk
"""

from .ResearchManager import create_research_manager
from .RiskMngmnt import create_risk_manager

__all__ = [
    'create_research_manager',
    'create_risk_manager'
]

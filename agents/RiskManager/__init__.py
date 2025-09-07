"""
Risk Management Agents

This module contains risk assessment agents:
- Aggressive Risk Analyst: High-risk, high-reward analysis
- Conservative Risk Analyst: Low-risk, stable analysis  
- Neutral Risk Analyst: Balanced risk assessment
"""

from .aggressive import create_risky_debator
from .conservative import create_safe_debator
from .Nuetral import create_neutral_debator

__all__ = [
    'create_risky_debator',
    'create_safe_debator',
    'create_neutral_debator'
]

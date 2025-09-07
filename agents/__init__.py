"""
Financial Trading Agents Package

This package contains various financial analysis agents including:
- Market analysts
- News analysts  
- Social media analysts
- Risk managers
- Researchers (bull/bear)
- Trading agents
"""

# Import all agent creation functions
from .analyst import (
    create_fundamentals_analyst,
    create_market_analyst, 
    create_news_analyst,
    create_social_media_analyst
)

from .researcher import (
    create_bull_researcher,
    create_bear_researcher
)

from .trader import (
    create_trader
)

from .Managers import (
    create_research_manager,
    create_risk_manager
)

from .RiskManager import (
    create_risky_debator,
    create_safe_debator,
    create_neutral_debator
)

from .utils.agent_utils import (
    create_msg_delete
)

__all__ = [
    # Analyst functions
    'create_fundamentals_analyst',
    'create_market_analyst', 
    'create_news_analyst',
    'create_social_media_analyst',
    # Researcher functions
    'create_bull_researcher',
    'create_bear_researcher',
    # Trader functions
    'create_trader',
    # Manager functions
    'create_research_manager',
    'create_risk_manager',
    # Risk management functions
    'create_risky_debator',
    'create_safe_debator',
    'create_neutral_debator',
    # Utility functions
    'create_msg_delete'
]
# TradingAgents/graph/setup.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

import json
from agents.utils.loader import import_from_string
from agents.utils.agent_states import AgentState
from agents.utils.agent_utils import Toolkit

from .ConditionalLogic import ConditionalLogic


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: ChatOpenAI,
        deep_thinking_llm: ChatOpenAI,
        toolkit: Toolkit,
        tool_nodes: Dict[str, ToolNode],
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        risk_manager_memory,
        conditional_logic: ConditionalLogic,
    ):
        """Initialize with required components."""
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.toolkit = toolkit
        self.tool_nodes = tool_nodes
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.risk_manager_memory = risk_manager_memory
        self.conditional_logic = conditional_logic

    def setup_graph(
        self, selected_analysts=["market", "social", "news", "fundamentals"]
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Options are:
                - "market": Market analyst
                - "social": Social media analyst
                - "news": News analyst
                - "fundamentals": Fundamentals analyst
        """
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        # Create analyst nodes
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        # Load agent factories from agents/registry.json
        import os
        registry_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agents', 'registry.json')
        with open(registry_path, 'r') as f:
            agents_config = json.load(f)

        utilities = agents_config.get("utilities", {})
        delete_factory = import_from_string(utilities.get("delete_messages", "agents.utils.agent_utils.create_msg_delete"))

        analysts_map = agents_config.get("analysts", {})
        for key in selected_analysts:
            if key in analysts_map:
                factory = import_from_string(analysts_map[key])
                analyst_nodes[key] = factory(self.quick_thinking_llm, self.toolkit)
                delete_nodes[key] = delete_factory()
                tool_nodes[key] = self.tool_nodes.get(key)

        # Create researcher and manager nodes
        bull_factory = import_from_string(agents_config["researchers"]["bull"])
        bear_factory = import_from_string(agents_config["researchers"]["bear"])
        research_manager_factory = import_from_string(agents_config["managers"]["research"])
        trader_factory = import_from_string(agents_config["trader"])

        bull_researcher_node = bull_factory(self.quick_thinking_llm, self.bull_memory)
        bear_researcher_node = bear_factory(self.quick_thinking_llm, self.bear_memory)
        research_manager_node = research_manager_factory(self.deep_thinking_llm, self.invest_judge_memory)
        trader_node = trader_factory(self.quick_thinking_llm, self.trader_memory)

        # Create risk analysis nodes
        risky_factory = import_from_string(agents_config["risk_roles"]["risky"])
        neutral_factory = import_from_string(agents_config["risk_roles"]["neutral"])
        safe_factory = import_from_string(agents_config["risk_roles"]["safe"])
        risk_manager_factory = import_from_string(agents_config["managers"]["risk"])

        risky_analyst = risky_factory(self.quick_thinking_llm)
        neutral_analyst = neutral_factory(self.quick_thinking_llm)
        safe_analyst = safe_factory(self.quick_thinking_llm)
        risk_manager_node = risk_manager_factory(self.deep_thinking_llm, self.risk_manager_memory)

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(f"{analyst_type.capitalize()} Analyst", node)
            workflow.add_node(
                f"Msg Clear {analyst_type.capitalize()}", delete_nodes[analyst_type]
            )
            workflow.add_node(f"tools_{analyst_type}", tool_nodes[analyst_type])

        # Add other nodes
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Risky Analyst", risky_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Safe Analyst", safe_analyst)
        workflow.add_node("Risk Judge", risk_manager_node)

        # Define edges
        # Start with the first analyst
        first_analyst = selected_analysts[0]
        workflow.add_edge(START, f"{first_analyst.capitalize()} Analyst")

        # Connect analysts in sequence
        for i, analyst_type in enumerate(selected_analysts):
            current_analyst = f"{analyst_type.capitalize()} Analyst"
            current_tools = f"tools_{analyst_type}"
            current_clear = f"Msg Clear {analyst_type.capitalize()}"

            # Add conditional edges for current analyst
            workflow.add_conditional_edges(
                current_analyst,
                getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current_analyst)

            # Connect to next analyst or to Bull Researcher if this is the last analyst
            if i < len(selected_analysts) - 1:
                next_analyst = f"{selected_analysts[i+1].capitalize()} Analyst"
                workflow.add_edge(current_clear, next_analyst)
            else:
                workflow.add_edge(current_clear, "Bull Researcher")

        # Add remaining edges
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Risky Analyst")
        workflow.add_conditional_edges(
            "Risky Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Safe Analyst": "Safe Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Safe Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Risky Analyst": "Risky Analyst",
                "Risk Judge": "Risk Judge",
            },
        )

        workflow.add_edge("Risk Judge", END)

        # Compile and return
        return workflow.compile()
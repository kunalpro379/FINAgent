# FINAgent

A modular, plug-and-play financial research and trading agent framework. It integrates market data tools, analysis agents, memory, a graph-based orchestration layer, and a Zerodha MCP bridge for execution and UI.

## Features
- Analysts for market, news, and social data
- Research and risk management managers
- Tools for data collection (Yahoo Finance, Google News, Reddit, Finnhub)
- Graph orchestration with signal processing and reflection
- Pluggable LLM provider(s)
- Persistent memory and NeonDB integration
- Zerodha MCP server/client bridge

## Project Structure
```
FINAgent/
  agents/                # Analysts, Researchers, Risk Managers, Trader
  data/                  # Local data assets/cache
  dataflows/             # Data pipelines and cached market data
  Langgraph/             # Graph orchestration and processing
  LLMs/                  # LLM provider integrations
  memory/                # Memory backends and registry
  NeonDB/                # Neon/Postgres utilities
  prompts/               # Prompt templates
  tools/                 # Data tools and registries
  ZerodhaMCP/            # MCP server/client integration for Zerodha
  main.py                # Entrypoint
  requirements.txt       # Python dependencies
  scripts/               # Utility scripts (e.g., registry validation)
```

The design follows Single Responsibility Principle (SRP) and a plug-and-play layout to simplify extension and maintenance.

## Prerequisites
- Python 3.10+
- Recommended: virtual environment (venv)

## Installation
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration
- Tools and API keys: check files under `tools/` (e.g., `FInnhub.py`, `GoogleNews.py`, `YFin.py`). Use environment variables where supported.
- Zerodha MCP config: `ZerodhaMCP/zerodha.json`.

## Run
- CLI/entrypoint:
```bash
python main.py
```
- Simple analysis example:
```bash
python simple_analysis.py
```

## Tests
```bash
python -m pytest -q
```

## Mermaid Workflow
The high-level system workflow is outlined below.
```mermaid
graph LR
  %% Data Sources and Tools
  subgraph DataTools["Tools"]
    YF["YFinance (tools/YFin.py)"]
    GN["Google News (tools/GoogleNews.py)"]
    RD["Reddit (tools/Reddit.py)"]
    FH["Finnhub (tools/FInnhub.py)"]
    SS["Stats (tools/StockStatistics.py)"]
  end

  %% Agents
  subgraph Agents["Agents"]
    subgraph Analysts
      MA["MarketAnalyst"]
      NA["NewsAnalyst"]
      SMA["SocialMediaAnalyst"]
      BA["BasicAnalyst"]
    end
    subgraph Research
      RM["ResearchManager"]
      BULL["Researcher: bull"]
      BEAR["Researcher: bear"]
    end
    subgraph Risk
      AGR["RiskManager: aggressive"]
      CON["RiskManager: conservative"]
      NTR["RiskManager: neutral"]
      RSK["RiskMngmnt"]
    end
    TRD["Trader"]
  end

  %% Orchestration & Memory
  subgraph Orchestration["Langgraph"]
    TG["TradingAgentGraph"]
    CL["ConditionalLogic"]
    SP["SignalProcessing"]
    RF["Reflection"]
    PG["Propagation"]
  end

  subgraph MemoryLayer["Memory & Storage"]
    MEM["Memory (memory/)"]
    NEON["NeonDB"]
  end

  subgraph MCP["Zerodha MCP"]
    SRV["MCP Server (ZerodhaMCP/server.py)"]
    CLI["MCP Client (ZerodhaMCP/agno_client.py)"]
  end

  %% LLMs
  LLM["LLMs (LLMs/groq)"]

  %% Data flow
  YF --> MA
  GN --> NA
  RD --> SMA
  FH --> MA
  SS --> BA

  MA --> RM
  NA --> RM
  SMA --> RM
  BA --> RM

  RM --> BULL
  RM --> BEAR
  BULL --> RSK
  BEAR --> RSK

  RSK --> AGR
  RSK --> CON
  RSK --> NTR

  AGR --> TRD
  CON --> TRD
  NTR --> TRD

  %% Orchestration interactions
  Agents --> TG
  TG --> CL
  TG --> SP
  TG --> RF
  TG --> PG
  CL --> TRD
  SP --> TRD
  RF --> Agents
  PG --> Agents

  %% Memory and storage
  Agents --> MEM
  TRD --> MEM
  MEM --> NEON

  %% LLM usage
  Agents --> LLM
  TG --> LLM

  %% MCP bridge
  TRD --> SRV
  SRV --> CLI
```

If you prefer a standalone diagram file, see `ignore/diagram.mmd` (and `ignore/mermaid_diagram.html` for a static render).

## Development Tips
- Keep each class focused (SRP) and prefer small, composable modules.
- Add new tools under `tools/` and register them in `tools/registry.json`.
- New agents should reside under `agents/` and use `agents/utils` helpers.
- Validate registries with:
```bash
python scripts/validate_registries.py
```

## License
Proprietary. All rights reserved.

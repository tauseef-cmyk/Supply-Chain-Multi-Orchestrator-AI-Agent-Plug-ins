# SCIQLab Supply Chain AI Agents — Claude Plugin Marketplace

A Claude Code / Cowork plugin marketplace that bundles three AI-powered supply chain agents into a single installable package.

## Quick Install

### Option 1: Add as a marketplace (Claude Code)

```bash
/plugin marketplace add tauseef-cmyk/Supply-Chain-Multi-Orchestrator-AI-Agent-Plug-ins
/plugin install sciqlab-supply-chain@sciqlab-supply-chain-marketplace
```

### Option 2: Install the .plugin file (Cowork)

Download `sciqlab-supply-chain.plugin` from the [Releases](https://github.com/tauseef-cmyk/Supply-Chain-Multi-Orchestrator-AI-Agent-Plug-ins/releases) page and open it in Claude Desktop / Cowork.

## What's Inside

### 1. Demand Exception Analyzer

Reads historical sales-vs-forecast data (CSV) and produces actionable exception reports.

- Calculates MAPE and WMAPE at SKU and Category level
- Flags consecutive exceptions (forecast error >30% for 2+ months)
- Detects systematic over-forecast or under-forecast bias
- Generates an executive summary ready for VP-level review
- Exports `demand_exceptions.csv` and `demand_summary.txt`

**Trigger phrases:** "demand exceptions", "forecast accuracy", "MAPE", "WMAPE", "forecast bias", "exception report", "planner review"

### 2. Supplier Risk Assessment

Two-step AI workflow that researches and scores suppliers across 6 risk dimensions.

- **Step 1 — Research:** Queries Tavily web search API for each supplier across Financial Health, Geopolitical Risk, ESG/Sustainability, Supply Continuity, Compliance/Sanctions, and Reputation
- **Step 2 — Score & Report:** Uses Claude API to score each supplier (1-10 per dimension), calculates weighted averages, and generates a color-coded Excel report with a Risk Dashboard and per-supplier detail sheets

**Trigger phrases:** "supplier risk", "vendor scoring", "supplier due diligence", "risk scorecard", "OTIF", "ESG scoring"

### 3. Multi-Agent Orchestrator

Coordinates both agents into a single integrated report for S&OP meetings.

- Runs demand analysis first, identifies CRITICAL/WATCH SKUs
- Runs supplier risk scoring only for problem SKUs
- Synthesizes an integrated action plan with priority matrix (P1-P4)
- Generates S&OP talking points ready for Monday meetings

**Trigger phrases:** "full analysis", "end-to-end review", "S&OP exception report with vendor scoring", "integrated supply chain report"

## Prerequisites

### Environment Variables

| Variable | Required For | Where to Get |
|----------|-------------|--------------|
| `ANTHROPIC_API_KEY` | Supplier Risk Assessment, Orchestrator | [console.anthropic.com](https://console.anthropic.com) |
| `TAVILY_API_KEY` | Supplier Risk Assessment (web research) | [tavily.com](https://tavily.com) — free tier available |

### Python Dependencies

```bash
pip install tavily-python anthropic openpyxl
```

The Demand Exception Analyzer uses only Python standard library (no extra packages needed).

## Sample Data Included

Each skill includes sample data files so you can try it immediately after installing:

- `demand_data_template.csv` — 6 SKUs x 6 months of sales vs forecast data
- `supplier_risk_assessment_sample.csv` — 10 global suppliers across various categories
- `sample_data.csv` — Combined demand + supplier data for orchestrator testing

## Repository Structure

```
.
├── .claude-plugin/
│   └── marketplace.json          # Marketplace catalog (required for /plugin marketplace add)
├── plugins/
│   └── sciqlab-supply-chain/
│       ├── .claude-plugin/
│       │   └── plugin.json       # Plugin manifest
│       ├── skills/
│       │   ├── demand-exception-analyzer/
│       │   │   ├── SKILL.md
│       │   │   ├── scripts/
│       │   │   │   └── demand_agent.py
│       │   │   └── assets/
│       │   │       └── demand_data_template.csv
│       │   ├── supplier-risk-assessment/
│       │   │   ├── SKILL.md
│       │   │   ├── supplier_analysis.py
│       │   │   ├── supplier_scoring.py
│       │   │   └── supplier_risk_assessment_sample.csv
│       │   └── multi-agent-orchestrator/
│       │       ├── SKILL.md
│       │       ├── orchestrator.py
│       │       └── sample_data.csv
│       └── requirements.txt
├── LICENSE
└── README.md
```

## Author

Built by **SCIQLab** — AI-powered supply chain intelligence.

## License

MIT License. See [LICENSE](LICENSE) for details.

---
name: supplier-risk-assessment
description: >
  Run a two-step supplier risk assessment: (1) research suppliers from a CSV using Tavily web search,
  (2) score each supplier across 6 risk dimensions using Claude API, and generate a color-coded Excel report.
  Use this skill when the user asks to "assess supplier risk", "score my suppliers", "supplier due diligence",
  "vendor risk report", "supplier risk scorecard", or uploads a CSV with supplier names, websites, and countries.
  Also trigger on mentions of "OTIF", "supplier financial health", "geopolitical risk", "ESG scoring",
  "supply continuity", or "compliance screening".
---

# Supplier Risk Assessment AI Agent

This skill performs an end-to-end supplier risk assessment workflow: web-based research followed by AI-powered scoring and Excel report generation.

## Prerequisites

The user must have the following environment variables set:
- `TAVILY_API_KEY` — free key from https://tavily.com
- `ANTHROPIC_API_KEY` — Anthropic API key

Required Python packages: `tavily-python`, `anthropic`, `openpyxl`

## Workflow

### Step 1 — Install dependencies

```bash
pip install tavily-python anthropic openpyxl --break-system-packages
```

### Step 2 — Prepare input data

The input CSV must have these columns: `supplier_name`, `website`, `country`, `category`

A sample CSV is bundled at `${CLAUDE_PLUGIN_ROOT}/skills/supplier-risk-assessment/supplier_risk_assessment_sample.csv`.

If the user provides their own CSV, copy it to the working directory. Otherwise use the sample for demo purposes.

### Step 3 — Run Market Research (supplier_analysis.py)

This script reads suppliers from the CSV and queries Tavily across 6 risk dimensions (Financial Health, Geopolitical Risk, ESG/Sustainability, Supply Continuity, Compliance/Sanctions, Reputation). Output: `supplier_research_results.json`.

```bash
cp ${CLAUDE_PLUGIN_ROOT}/skills/supplier-risk-assessment/supplier_analysis.py ./
cp ${CLAUDE_PLUGIN_ROOT}/skills/supplier-risk-assessment/supplier_risk_assessment_sample.csv ./
python supplier_analysis.py
```

### Step 4 — Run Scoring & Report Generation (supplier_scoring.py)

This script reads the research JSON, uses Claude to score each supplier (1-10 per dimension with weighted averages), and generates `supplier_risk_report.xlsx` with a color-coded dashboard and per-supplier detail sheets.

```bash
cp ${CLAUDE_PLUGIN_ROOT}/skills/supplier-risk-assessment/supplier_scoring.py ./
python supplier_scoring.py
```

### Step 5 — Deliver results

Copy `supplier_risk_report.xlsx` to the user's workspace folder and present a summary of highest-risk suppliers.

## Input Format

CSV file with columns: `supplier_name`, `website`, `country`, `category`

## Output

- `supplier_research_results.json` — raw research data
- `supplier_risk_report.xlsx` — color-coded Excel report with:
  - **Risk Dashboard** sheet (summary with all suppliers)
  - **Per-supplier detail sheets** (scores, evidence, recommendation)

## Risk Dimensions & Weights

| Dimension | Weight |
|---|---|
| Financial Health | 25% |
| Geopolitical Risk | 20% |
| Supply Continuity | 20% |
| ESG / Sustainability | 15% |
| Compliance / Sanctions | 10% |
| Reputation | 10% |

## Risk Rating Scale

- **Low** (1-3): Green
- **Medium** (4-6): Amber
- **High** (7-10): Red

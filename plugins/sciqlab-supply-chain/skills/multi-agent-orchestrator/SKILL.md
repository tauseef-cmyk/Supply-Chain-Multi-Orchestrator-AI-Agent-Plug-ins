---
name: multi-agent-orchestrator
description: >
  Use this skill when a supply chain query requires BOTH demand planning analysis AND supplier risk
  assessment together. Triggers on "full analysis", "demand and supplier", "end-to-end review",
  "S&OP exception report with vendor scoring", "integrated supply chain report", "full supply chain
  analysis", or when the user wants a combined demand + supplier risk view for S&OP meetings.
  This orchestrator coordinates the demand agent and supplier agent into a single integrated report.
---

# Multi-Agent Supply Chain Orchestrator

This skill coordinates both the Demand Exception Analyzer and Supplier Risk Assessment into a single integrated workflow, producing a unified report for S&OP meetings.

## Prerequisites

- `ANTHROPIC_API_KEY` environment variable must be set
- Python 3.10+ with the `anthropic` package installed

```bash
pip install anthropic --break-system-packages
```

## How It Works

The orchestrator runs three sequential steps:

### Step 1 — Demand Agent
- Analyzes SKU-level demand data
- Calculates MAPE per SKU
- Flags exceptions over 20% error
- Classifies each SKU as CRITICAL / WATCH / STABLE

### Step 2 — Supplier Agent
For CRITICAL and WATCH SKUs only:
- Scores supplier risk 1-10 across: OTIF, quality, financial stability, geography, capacity, tenure
- Classifies each supplier: LOW / MEDIUM / HIGH risk

### Step 3 — Synthesize Integrated Report
Combines demand exceptions and supplier risk into a priority matrix:
- P1 URGENT: CRITICAL demand + HIGH supplier risk
- P2 HIGH: CRITICAL demand + MEDIUM supplier risk
- P3 MEDIUM: WATCH demand + HIGH supplier risk
- P4 LOW: STABLE demand + any supplier risk level

## How to Run

### Option A: With user-provided data

If the user provides demand and supplier CSVs:

```bash
cp ${CLAUDE_PLUGIN_ROOT}/skills/multi-agent-orchestrator/orchestrator.py ./
python orchestrator.py
```

Before running, modify the `__main__` block to load the user's CSV files using `load_csv_data()`.

### Option B: With sample data (demo)

The script includes built-in sample data for demonstration. Copy and run directly:

```bash
cp ${CLAUDE_PLUGIN_ROOT}/skills/multi-agent-orchestrator/orchestrator.py ./
cp ${CLAUDE_PLUGIN_ROOT}/skills/multi-agent-orchestrator/sample_data.csv ./
python orchestrator.py
```

## Output

The orchestrator produces a formatted report with 5 sections:

1. **Executive Summary** — Overall supply chain health (GREEN/AMBER/RED), P1-P4 counts, top 3 risks, S&OP focus areas
2. **Demand Exception Table** — SKU-level forecast accuracy, bias, and classification
3. **Supplier Risk Scorecard** — Per-supplier scores across risk dimensions
4. **Integrated Action Plan** — Priority matrix with recommended actions, owners, and due dates
5. **S&OP Talking Points** — 3-5 bullet points ready for the Monday S&OP meeting

Copy the report output to the user's workspace folder and present the executive summary in chat.

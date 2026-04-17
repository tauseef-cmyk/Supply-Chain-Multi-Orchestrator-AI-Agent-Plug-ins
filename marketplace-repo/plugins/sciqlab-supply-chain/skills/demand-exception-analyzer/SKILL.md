---
name: demand-exception-analyzer
description: >
  Use this skill whenever a demand planning analyst needs to analyze historical
  sales vs forecast data, calculate forecast accuracy metrics (MAPE, WMAPE), detect forecast
  bias, or identify SKU-level exceptions requiring human planner review. Trigger on any mention
  of "demand exceptions", "forecast accuracy", "MAPE", "WMAPE", "forecast bias", "planner review",
  "demand agent", "sales vs forecast", "exception report", "forecast error", "demand planning analysis",
  "bias detection", or when the user uploads a CSV with columns like SKU, Actual_Sales, and Forecast.
  Also trigger when asked to generate an executive summary of forecast performance or flag problem SKUs.
  Works with any demand planning dataset that follows the expected CSV format.
---

# Demand Exception Analyzer

This skill runs a Python-based demand planning agent that reads historical sales-vs-forecast data and produces actionable exception reports for human planner review.

## What It Does

Given a CSV file with SKU-level actuals and forecasts, the agent:

1. **Calculates accuracy metrics** — MAPE and WMAPE at both SKU and Category level
2. **Flags consecutive exceptions** — Any SKU where absolute forecast error exceeds 30% for 2+ consecutive months
3. **Detects forecast bias** — Identifies systematic over-forecasting or under-forecasting patterns (>2 consistent periods)
4. **Generates an executive summary** — A plain-language report a VP of Supply Chain can read in 30 seconds
5. **Exports results** — `demand_exceptions.csv` (detailed metrics) and `demand_summary.txt` (executive brief)

## Expected Input Format

The input CSV must have these columns (order doesn't matter, but names must match exactly):

| Column | Type | Description |
|--------|------|-------------|
| SKU | Text | Unique SKU identifier (e.g., MFG-0001) |
| Product_Name | Text | Human-readable product name |
| Category | Text | Product category for roll-up metrics |
| Date | Date | Period date in YYYY-MM-DD format |
| Actual_Sales | Numeric | Actual units sold in that period |
| Forecast | Numeric | Forecasted units for that period |

A sample template CSV is bundled at `assets/demand_data_template.csv`. If the user needs help understanding the format or wants a blank template, provide this file.

## How to Run

### Step 1: Locate or request the input data

If the user hasn't provided a CSV, ask them to upload one or point to a file path. If they want to see the expected format first, read and share the sample template from `assets/demand_data_template.csv`.

### Step 2: Copy script and data to working directory

Copy `scripts/demand_agent.py` from `${CLAUDE_PLUGIN_ROOT}/skills/demand-exception-analyzer/scripts/` and the user's CSV (renamed to `demand_data.csv`) into the working directory:

```bash
cp ${CLAUDE_PLUGIN_ROOT}/skills/demand-exception-analyzer/scripts/demand_agent.py ./
cp <user-csv-path> ./demand_data.csv
```

### Step 3: Execute the agent

```bash
python demand_agent.py
```

The script will:
- Print progress messages to console
- Generate `demand_exceptions.csv` in the working directory
- Generate `demand_summary.txt` in the working directory
- Print the executive summary to console

### Step 4: Deliver results to the user

1. Copy both output files to the user's workspace folder
2. Present the executive summary in the chat — this is the most important output for quick consumption
3. Link the detailed CSV for deeper analysis
4. If the user wants an Excel version, use the xlsx skill to convert `demand_exceptions.csv` into a formatted spreadsheet

## Key Metrics Explained

Use these definitions when the user asks questions about the output:

- **MAPE (Mean Absolute Percentage Error)**: Average of |Actual - Forecast| / Actual across all periods. Excludes zero-actual periods. Lower is better; under 20% is generally acceptable for manufacturing.
- **WMAPE (Weighted MAPE)**: Sum of |Actual - Forecast| / Sum of Actual. Gives more weight to high-volume periods. Often preferred over MAPE because it isn't distorted by low-volume SKUs.
- **Forecast Bias**: Mean of (Forecast - Actual). Positive = over-forecasting (risk of excess inventory). Negative = under-forecasting (risk of stock-outs). Flagged when bias direction is consistent for >2 periods.
- **Consecutive Exception**: A SKU where forecast error exceeds 30% for 2 or more months in a row — these need immediate human planner attention.

## Interpreting Results for Stakeholders

When presenting findings, frame them in supply chain impact terms:

- Over-forecast bias → excess inventory, carrying costs, potential obsolescence
- Under-forecast bias → stock-outs, missed revenue, expediting costs
- High MAPE categories → unreliable planning inputs, need for safety stock buffers
- Consecutive exceptions → systemic model failure, not random noise — requires root cause investigation

## Recommended Follow-Up Actions

Based on the exception patterns, suggest these actions:

| Pattern | Recommended Action |
|---------|-------------------|
| Overall MAPE > 30% | Prioritize S&OP review for top exception SKUs; add statistical safety stock buffers |
| >25% SKUs with consecutive exceptions | Investigate demand volatility drivers (promotions, seasonality, NPI); refresh forecasting models |
| Persistent over-forecast bias | Apply bias-correction factor; reduce safety stock for affected items |
| Persistent under-forecast bias | Increase safety stock; review lead times immediately |
| All metrics within bounds | Continue monthly accuracy reviews; monitor for emerging patterns |

pythonimport os
import sys
import json
import csv
from anthropic import Anthropic

client = Anthropic()

def run_demand_agent(demand_data: list) -> dict:
    """Run demand exception analysis on SKU data."""
    prompt = f"""You are a Demand Planning Agent for Maple Manufacturing Ltd.

Analyze this demand data and return a JSON object with this exact structure:
{{
  "exceptions": [
    {{
      "sku": "SKU001",
      "actual": 450,
      "forecast": 380,
      "mape": 18.4,
      "bias": "UNDER",
      "classification": "WATCH"
    }}
  ],
  "summary": "Brief summary of demand health"
}}

Classification rules:
- CRITICAL: MAPE > 30% OR 3+ consecutive misses
- WATCH: MAPE 20-30%
- STABLE: MAPE < 20%

Bias: OVER = forecasting too high, UNDER = forecasting too low

Demand data:
{json.dumps(demand_data, indent=2)}

Return ONLY valid JSON, no other text."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    result_text = response.content[0].text.strip()
    if result_text.startswith("```"):
        result_text = result_text.split("```")[1]
        if result_text.startswith("json"):
            result_text = result_text[4:]
    
    return json.loads(result_text)


def run_supplier_agent(supplier_data: list, critical_skus: list) -> dict:
    """Run supplier risk scoring for critical/watch SKUs only."""
    relevant = [s for s in supplier_data if s.get("sku") in critical_skus]
    
    if not relevant:
        return {"suppliers": [], "summary": "No supplier risks to assess"}
    
    prompt = f"""You are a Supplier Risk Assessment Agent for Maple Manufacturing Ltd.

Score each supplier and return a JSON object with this exact structure:
{{
  "suppliers": [
    {{
      "supplier": "Supplier A",
      "sku": "SKU001",
      "scores": {{
        "otif": 6,
        "quality": 7,
        "financial": 7,
        "geography": 5,
        "capacity": 7,
        "tenure": 8
      }},
      "total_score": 6.7,
      "risk_level": "MEDIUM",
      "top_risk_factor": "Geography - Mexico operations"
    }}
  ],
  "summary": "Brief supplier risk summary"
}}

Scoring: 1=Very High Risk, 10=Very Low Risk
Risk levels: HIGH (1-4), MEDIUM (5-7), LOW (8-10)

Supplier data:
{json.dumps(relevant, indent=2)}

Return ONLY valid JSON, no other text."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    result_text = response.content[0].text.strip()
    if result_text.startswith("```"):
        result_text = result_text.split("```")[1]
        if result_text.startswith("json"):
            result_text = result_text[4:]
    
    return json.loads(result_text)


def synthesize_report(demand_result: dict, supplier_result: dict) -> str:
    """Combine demand and supplier results into integrated report."""
    prompt = f"""You are the Supply Chain Orchestrator for Maple Manufacturing Ltd.

Given these results from the Demand Agent and Supplier Agent, produce a formatted report.

DEMAND ANALYSIS RESULTS:
{json.dumps(demand_result, indent=2)}

SUPPLIER RISK RESULTS:
{json.dumps(supplier_result, indent=2)}

Produce a report with these 5 sections:

## Section 1: Executive Summary
- Overall supply chain health (GREEN/AMBER/RED)
- Count of P1/P2/P3/P4 items
- Top 3 risks requiring immediate attention
- Recommended focus for this week's S&OP

## Section 2: Demand Exception Table
| SKU | Actual | Forecast | MAPE% | Bias | Classification |
(fill with data)

## Section 3: Supplier Risk Scorecard  
| Supplier | SKU | Risk Score | Risk Level | Top Risk Factor |
(fill with data, or "No critical suppliers to assess" if none)

## Section 4: Integrated Action Plan
Priority matrix:
- P1 URGENT: CRITICAL demand + HIGH supplier risk
- P2 HIGH: CRITICAL demand + MEDIUM supplier risk  
- P3 MEDIUM: WATCH demand + HIGH supplier risk
- P4 LOW: STABLE demand + any

| Priority | SKU | Supplier | Issue | Recommended Action | Owner | Due |
(fill with data)

## Section 5: S&OP Talking Points
3-5 bullet points for Monday S&OP meeting"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


def run_orchestrator(demand_data: list, supplier_data: list) -> str:
    """Main orchestrator function."""
    print("\n🔄 Step 1: Running Demand Agent...")
    demand_result = run_demand_agent(demand_data)
    
    critical_skus = [
        e["sku"] for e in demand_result.get("exceptions", [])
        if e["classification"] in ["CRITICAL", "WATCH"]
    ]
    print(f"   Found {len(critical_skus)} CRITICAL/WATCH SKUs: {critical_skus}")
    
    print("\n🔄 Step 2: Running Supplier Agent...")
    supplier_result = run_supplier_agent(supplier_data, critical_skus)
    print(f"   Assessed {len(supplier_result.get('suppliers', []))} suppliers")
    
    print("\n🔄 Step 3: Synthesizing Report...")
    report = synthesize_report(demand_result, supplier_result)
    
    return report


def load_csv_data(filepath: str) -> list:
    """Load data from CSV file."""
    data = []
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


if __name__ == "__main__":
    # Sample data for testing
    demand_data = [
        {"sku": "SKU001", "actual": 450, "forecast": 380},
        {"sku": "SKU002", "actual": 120, "forecast": 145},
        {"sku": "SKU003", "actual": 890, "forecast": 620},
        {"sku": "SKU004", "actual": 200, "forecast": 195},
    ]
    
    supplier_data = [
        {"sku": "SKU001", "supplier": "Supplier A", "otif": 0.78, "tenure_years": 3, "country": "Mexico"},
        {"sku": "SKU003", "supplier": "Supplier B", "otif": 0.91, "tenure_years": 1, "country": "China"},
    ]
    
    report = run_orchestrator(demand_data, supplier_data)
    print("\n" + "="*60)
    print("INTEGRATED SUPPLY CHAIN REPORT")
    print("="*60)
    print(report)
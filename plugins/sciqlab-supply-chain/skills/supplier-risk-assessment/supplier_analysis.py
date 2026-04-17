"""
Supplier Risk Assessment — Market Research Agent
Reads suppliers from CSV and gathers risk intelligence via Tavily web search API.
Output: supplier_research_results.json
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

try:
    from tavily import TavilyClient
except ImportError:
    print("ERROR: tavily-python not installed. Run: pip install tavily-python")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CSV_INPUT = Path(__file__).parent / "supplier_risk_assessment_sample.csv"
JSON_OUTPUT = Path(__file__).parent / "supplier_research_results.json"

RISK_DIMENSIONS = [
    {
        "key": "financial_health",
        "label": "Financial Health",
        "query_template": "{supplier} financial performance revenue earnings credit rating 2024 2025",
    },
    {
        "key": "geopolitical_risk",
        "label": "Geopolitical Risk",
        "query_template": "{supplier} {country} sanctions trade restrictions political risk geopolitical",
    },
    {
        "key": "esg_sustainability",
        "label": "ESG / Sustainability",
        "query_template": "{supplier} ESG sustainability environmental violations labor issues governance",
    },
    {
        "key": "supply_continuity",
        "label": "Supply Continuity",
        "query_template": "{supplier} supply chain disruption shortage capacity production issues",
    },
    {
        "key": "compliance_sanctions",
        "label": "Compliance / Sanctions",
        "query_template": "{supplier} regulatory compliance violations fines sanctions legal issues",
    },
    {
        "key": "reputation",
        "label": "Reputation",
        "query_template": "{supplier} news controversy scandal reputation brand risk",
    },
]


def load_suppliers(csv_path: Path) -> list[dict]:
    """Load supplier list from CSV."""
    suppliers = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            suppliers.append(
                {
                    "supplier_name": row["supplier_name"].strip(),
                    "website": row["website"].strip(),
                    "country": row["country"].strip(),
                    "category": row["category"].strip(),
                }
            )
    return suppliers


def research_supplier(client: TavilyClient, supplier: dict) -> dict:
    """Run web searches for each risk dimension and collect results."""
    name = supplier["supplier_name"]
    country = supplier["country"]
    print(f"\n{'='*60}")
    print(f"  Researching: {name} ({country})")
    print(f"{'='*60}")

    research = {
        "supplier_name": name,
        "website": supplier["website"],
        "country": country,
        "category": supplier["category"],
        "research": {},
    }

    for dim in RISK_DIMENSIONS:
        query = dim["query_template"].format(supplier=name, country=country)
        print(f"  [{dim['label']}] Searching: {query[:80]}...")

        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_answer=True,
            )

            sources = []
            for result in response.get("results", []):
                sources.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", "")[:500],
                    }
                )

            research["research"][dim["key"]] = {
                "label": dim["label"],
                "answer": response.get("answer", "No summary available."),
                "sources": sources,
            }
            print(f"    -> Found {len(sources)} sources")

        except Exception as e:
            print(f"    -> ERROR: {e}")
            research["research"][dim["key"]] = {
                "label": dim["label"],
                "answer": f"Search failed: {e}",
                "sources": [],
            }

        time.sleep(1)  # rate-limit courtesy

    return research


def main():
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("ERROR: Set TAVILY_API_KEY environment variable.")
        print("  Get a free key at https://tavily.com")
        sys.exit(1)

    client = TavilyClient(api_key=api_key)
    suppliers = load_suppliers(CSV_INPUT)
    print(f"Loaded {len(suppliers)} suppliers from {CSV_INPUT.name}")

    all_results = []
    for i, supplier in enumerate(suppliers, 1):
        print(f"\n[{i}/{len(suppliers)}]", end="")
        result = research_supplier(client, supplier)
        all_results.append(result)

    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  Research complete! Results saved to: {JSON_OUTPUT.name}")
    print(f"  Suppliers analyzed: {len(all_results)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

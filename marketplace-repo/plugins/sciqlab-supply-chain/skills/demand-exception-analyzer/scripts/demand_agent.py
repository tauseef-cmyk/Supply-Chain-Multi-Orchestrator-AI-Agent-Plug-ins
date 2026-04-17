"""
demand_agent.py
---------------
Reads demand planning data, computes accuracy metrics, flags forecast exceptions
and bias patterns, exports results, and prints an executive summary.

Input  : demand_data.csv  (SKU, Product_Name, Category, Date, Actual_Sales, Forecast)
Outputs: demand_exceptions.csv  – per-SKU & per-category metrics + flags
         demand_summary.txt     – plain-language executive summary
"""

import csv
import math
import os
from collections import defaultdict
from datetime import datetime


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_data(filepath: str) -> list[dict]:
    """Load CSV and return list of row dicts with typed numeric fields."""
    rows = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["Actual_Sales"] = float(row["Actual_Sales"])
            row["Forecast"]     = float(row["Forecast"])
            row["Date"]         = datetime.strptime(row["Date"].strip(), "%Y-%m-%d")
            rows.append(row)
    return rows


def save_csv(filepath: str, fieldnames: list[str], rows: list[dict]) -> None:
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Metric calculations
# ---------------------------------------------------------------------------

def mape(actuals: list[float], forecasts: list[float]) -> float:
    """Mean Absolute Percentage Error (excludes zero-actual periods)."""
    errors = [
        abs(a - f) / a
        for a, f in zip(actuals, forecasts)
        if a != 0
    ]
    return (sum(errors) / len(errors)) * 100 if errors else float("nan")


def wmape(actuals: list[float], forecasts: list[float]) -> float:
    """Weighted MAPE = sum(|A-F|) / sum(A) * 100."""
    total_actual = sum(actuals)
    if total_actual == 0:
        return float("nan")
    total_abs_error = sum(abs(a - f) for a, f in zip(actuals, forecasts))
    return (total_abs_error / total_actual) * 100


# ---------------------------------------------------------------------------
# Exception flags
# ---------------------------------------------------------------------------

def flag_consecutive_exceptions(
    dates: list[datetime],
    actuals: list[float],
    forecasts: list[float],
    threshold: float = 30.0,
    min_consecutive: int = 2,
) -> bool:
    """
    Return True if the absolute % error exceeds `threshold` for
    `min_consecutive` or more consecutive periods (sorted by date).
    """
    paired = sorted(zip(dates, actuals, forecasts), key=lambda x: x[0])
    streak = 0
    for _, actual, forecast in paired:
        if actual == 0:
            streak = 0
            continue
        pct_error = abs(actual - forecast) / actual * 100
        if pct_error > threshold:
            streak += 1
            if streak >= min_consecutive:
                return True
        else:
            streak = 0
    return False


# ---------------------------------------------------------------------------
# Bias analysis
# ---------------------------------------------------------------------------

def compute_bias_summary(actuals: list[float], forecasts: list[float]) -> tuple[float, str]:
    """
    Returns (mean_bias, bias_label).
    bias = mean(Forecast - Actual)
    Label: 'over-forecast bias' | 'under-forecast bias' | 'neutral'
    Uses >2 *consistent* periods (same sign) to assign a label.
    """
    biases = [f - a for a, f in zip(actuals, forecasts)]
    mean_b = sum(biases) / len(biases) if biases else 0.0

    over_count  = sum(1 for b in biases if b > 0)
    under_count = sum(1 for b in biases if b < 0)

    if over_count > 2 and over_count > under_count:
        label = "over-forecast bias"
    elif under_count > 2 and under_count > over_count:
        label = "under-forecast bias"
    else:
        label = "neutral"

    return mean_b, label


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def process_skus(rows: list[dict]) -> tuple[list[dict], dict]:
    """
    Group rows by SKU, compute metrics, return:
      - sku_results  : list of per-SKU metric dicts
      - sku_lookup   : {sku: metric_dict}  (for summary)
    """
    by_sku: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_sku[row["SKU"].strip()].append(row)

    sku_results = []
    sku_lookup  = {}

    for sku, records in by_sku.items():
        records_sorted = sorted(records, key=lambda r: r["Date"])
        actuals   = [r["Actual_Sales"] for r in records_sorted]
        forecasts = [r["Forecast"]     for r in records_sorted]
        dates     = [r["Date"]         for r in records_sorted]

        sku_mape  = mape(actuals, forecasts)
        sku_wmape = wmape(actuals, forecasts)
        exception = flag_consecutive_exceptions(dates, actuals, forecasts)
        mean_bias, bias_label = compute_bias_summary(actuals, forecasts)

        result = {
            "SKU":                sku,
            "Product_Name":       records_sorted[0]["Product_Name"].strip(),
            "Category":           records_sorted[0]["Category"].strip(),
            "Periods_Analyzed":   len(records_sorted),
            "MAPE_%":             round(sku_mape,  2),
            "WMAPE_%":            round(sku_wmape, 2),
            "Mean_Bias":          round(mean_bias, 2),
            "Bias_Summary":       bias_label,
            "Consecutive_Exception": "YES" if exception else "NO",
        }
        sku_results.append(result)
        sku_lookup[sku] = result

    return sku_results, sku_lookup


def process_categories(rows: list[dict]) -> list[dict]:
    """Aggregate metrics by Category."""
    by_cat: dict[str, dict[str, list]] = defaultdict(lambda: {"actuals": [], "forecasts": [], "skus": set()})
    for row in rows:
        cat = row["Category"].strip()
        by_cat[cat]["actuals"].append(row["Actual_Sales"])
        by_cat[cat]["forecasts"].append(row["Forecast"])
        by_cat[cat]["skus"].add(row["SKU"].strip())

    cat_results = []
    for cat, data in by_cat.items():
        cat_results.append({
            "Category":         cat,
            "SKU_Count":        len(data["skus"]),
            "MAPE_%":           round(mape(data["actuals"],  data["forecasts"]), 2),
            "WMAPE_%":          round(wmape(data["actuals"], data["forecasts"]), 2),
        })
    return cat_results


# ---------------------------------------------------------------------------
# Executive summary
# ---------------------------------------------------------------------------

def build_executive_summary(
    sku_results:  list[dict],
    cat_results:  list[dict],
    all_actuals:  list[float],
    all_forecasts: list[float],
) -> str:
    total_skus      = len(sku_results)
    overall_mape    = mape(all_actuals, all_forecasts)
    overall_wmape   = wmape(all_actuals, all_forecasts)
    exceptions      = [r for r in sku_results if r["Consecutive_Exception"] == "YES"]
    num_exceptions  = len(exceptions)

    over_bias_skus  = [r for r in sku_results if r["Bias_Summary"] == "over-forecast bias"]
    under_bias_skus = [r for r in sku_results if r["Bias_Summary"] == "under-forecast bias"]

    # Top 3 problem SKUs by MAPE (ignoring NaN)
    ranked = sorted(
        [r for r in sku_results if not math.isnan(r["MAPE_%"])],
        key=lambda r: r["MAPE_%"],
        reverse=True,
    )
    top3 = ranked[:3]

    # Recommended action
    if overall_mape > 30:
        recommendation = (
            "Overall forecast accuracy is below acceptable thresholds (MAPE > 30%). "
            "Prioritise a collaborative S&OP review for the top exception SKUs and "
            "consider adding statistical safety stock buffers while models are recalibrated."
        )
    elif num_exceptions > total_skus * 0.25:
        recommendation = (
            "More than 25% of SKUs show consecutive forecast exceptions. "
            "Investigate demand volatility drivers (promotions, seasonality, NPI) "
            "and refresh forecasting models for affected categories."
        )
    elif over_bias_skus:
        recommendation = (
            f"{len(over_bias_skus)} SKU(s) show persistent over-forecast bias, risking excess inventory. "
            "Review the demand assumptions and apply a bias-correction factor or "
            "adjust safety stock policies downward for these items."
        )
    elif under_bias_skus:
        recommendation = (
            f"{len(under_bias_skus)} SKU(s) show persistent under-forecast bias, risking stock-outs. "
            "Increase safety stock levels and review lead times for these SKUs immediately."
        )
    else:
        recommendation = (
            "Forecast performance is within acceptable bounds. "
            "Continue monthly accuracy reviews and monitor for emerging volatility patterns."
        )

    lines = [
        "=" * 65,
        "  DEMAND PLANNING AGENT — EXECUTIVE SUMMARY",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 65,
        "",
        f"  Total SKUs Analysed   : {total_skus}",
        f"  Overall MAPE          : {overall_mape:.1f}%",
        f"  Overall WMAPE         : {overall_wmape:.1f}%",
        f"  Forecast Exceptions   : {num_exceptions} SKU(s) flagged",
        f"  Over-Forecast Bias    : {len(over_bias_skus)} SKU(s)",
        f"  Under-Forecast Bias   : {len(under_bias_skus)} SKU(s)",
        "",
        "  CATEGORY SUMMARY",
        "  " + "-" * 55,
    ]
    for c in sorted(cat_results, key=lambda x: x["MAPE_%"], reverse=True):
        lines.append(
            f"  {c['Category']:<25} MAPE {c['MAPE_%']:>6.1f}%   "
            f"WMAPE {c['WMAPE_%']:>6.1f}%   SKUs {c['SKU_Count']}"
        )

    lines += [
        "",
        "  TOP 3 PROBLEM SKUs (by MAPE)",
        "  " + "-" * 55,
    ]
    for i, r in enumerate(top3, 1):
        lines.append(
            f"  {i}. {r['SKU']:<12} {r['Product_Name']:<30} "
            f"MAPE {r['MAPE_%']:.1f}%   {r['Bias_Summary']}"
        )

    if exceptions:
        lines += [
            "",
            "  CONSECUTIVE EXCEPTION SKUs (error >30% for 2+ months)",
            "  " + "-" * 55,
        ]
        for r in exceptions:
            lines.append(f"  • {r['SKU']:<12} {r['Product_Name']}")

    lines += [
        "",
        "  RECOMMENDED ACTION",
        "  " + "-" * 55,
        f"  {recommendation}",
        "",
        "=" * 65,
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    input_file      = "demand_data.csv"
    exceptions_file = "demand_exceptions.csv"
    summary_file    = "demand_summary.txt"

    if not os.path.exists(input_file):
        raise FileNotFoundError(
            f"'{input_file}' not found. "
            "Place the demand data CSV in the same directory as demand_agent.py."
        )

    print(f"[demand_agent] Loading data from '{input_file}' ...")
    rows = load_data(input_file)
    print(f"[demand_agent] {len(rows)} rows loaded.")

    # -- SKU metrics ----------------------------------------------------------
    sku_results, _ = process_skus(rows)

    # -- Category metrics -----------------------------------------------------
    cat_results = process_categories(rows)

    # -- Build combined export ------------------------------------------------
    # Flatten: per-SKU rows + per-category summary rows (marked clearly)
    sku_fields = [
        "Row_Type", "SKU", "Product_Name", "Category",
        "Periods_Analyzed", "MAPE_%", "WMAPE_%",
        "Mean_Bias", "Bias_Summary", "Consecutive_Exception",
    ]

    export_rows = []
    for r in sorted(sku_results, key=lambda x: x["MAPE_%"] if not math.isnan(x["MAPE_%"]) else -1, reverse=True):
        export_rows.append({**{"Row_Type": "SKU"}, **r})

    # Separator-ish blank row then category rows
    cat_fields_map = {
        "Row_Type": "CATEGORY_SUMMARY",
        "SKU": "",
        "Product_Name": "",
        "Category": "",
        "Periods_Analyzed": "",
        "MAPE_%": "",
        "WMAPE_%": "",
        "Mean_Bias": "",
        "Bias_Summary": "",
        "Consecutive_Exception": "",
    }
    export_rows.append(cat_fields_map)  # blank divider row

    for c in sorted(cat_results, key=lambda x: x["MAPE_%"], reverse=True):
        export_rows.append({
            "Row_Type":            "CATEGORY_SUMMARY",
            "SKU":                 "",
            "Product_Name":        "",
            "Category":            c["Category"],
            "Periods_Analyzed":    c["SKU_Count"],
            "MAPE_%":              c["MAPE_%"],
            "WMAPE_%":             c["WMAPE_%"],
            "Mean_Bias":           "",
            "Bias_Summary":        "",
            "Consecutive_Exception": "",
        })

    save_csv(exceptions_file, sku_fields, export_rows)
    print(f"[demand_agent] Exceptions file saved -> '{exceptions_file}'")

    # -- Executive summary ----------------------------------------------------
    all_actuals   = [r["Actual_Sales"] for r in rows]
    all_forecasts = [r["Forecast"]     for r in rows]

    summary = build_executive_summary(sku_results, cat_results, all_actuals, all_forecasts)

    print("\n" + summary)

    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary + "\n")
    print(f"\n[demand_agent] Summary saved -> '{summary_file}'")


if __name__ == "__main__":
    main()


import pandas as pd

from tools.inventory_tools import get_reorder_suggestions
from tools.sales_tools import (
    get_slow_moving_products,
    compare_branch_sales,
    get_category_sales,

)


def get_category_revenue_metrics(
    sales,
    inventory,
    start_date,
    end_date,
    branch=None
):
    """
    Calculate category revenue, units sold, transactions
    and percentage contribution using actual sales data.
    """

    category_sales = get_category_sales(
        sales,
        inventory,
        start_date,
        end_date,
        branch=branch
    )

    if category_sales.empty:
        return {
            "status": "no_data",
            "message": "No category sales found for this period.",
            "categories": [],
            "total_revenue": 0.0
        }

    result = category_sales.copy()

    result["revenue"] = pd.to_numeric(
        result["revenue"],
        errors="coerce"
    ).fillna(0.0)

    total_revenue = float(result["revenue"].sum())

    if total_revenue != 0:
        result["revenue_share_percent"] = (
            result["revenue"] / total_revenue * 100
        )
    else:
        result["revenue_share_percent"] = 0.0

    return {
        "status": "success",
        "period_start": str(start_date),
        "period_end": str(end_date),
        "branch": branch or "All branches",
        "total_revenue": total_revenue,
        "categories": result.to_dict(orient="records")
    }


def compare_category_revenue(
    sales,
    inventory,
    start_date,
    end_date,
    category_a,
    category_b
):
    """
    Compare two categories using actual category sales.

    Percentage change is calculated relative to category_b.
    """

    if not category_a.strip() or not category_b.strip():
        raise ValueError("Both category names are required.")

    if category_a.strip().casefold() == category_b.strip().casefold():
        raise ValueError("Please provide two different categories.")

    metrics = get_category_revenue_metrics(
        sales,
        inventory,
        start_date,
        end_date
    )

    categories = metrics["categories"]

    category_lookup = {
        str(item["category"]).strip().casefold(): item
        for item in categories
    }

    key_a = category_a.strip().casefold()
    key_b = category_b.strip().casefold()

    missing = [
        name
        for name, key in [
            (category_a, key_a),
            (category_b, key_b)
        ]
        if key not in category_lookup
    ]

    if missing:
        return {
            "status": "no_data",
            "message": "One or both categories were not found.",
            "missing_categories": missing,
            "period_start": str(start_date),
            "period_end": str(end_date)
        }

    revenue_a = float(category_lookup[key_a]["revenue"])
    revenue_b = float(category_lookup[key_b]["revenue"])

    difference = revenue_a - revenue_b

    if revenue_b != 0:
        percentage_change = (
            difference / revenue_b
        ) * 100

        revenue_ratio = revenue_a / revenue_b
    else:
        percentage_change = None
        revenue_ratio = None

    return {
        "status": "success",
        "period_start": str(start_date),
        "period_end": str(end_date),
        "category_a": category_a,
        "category_b": category_b,
        "category_a_revenue": revenue_a,
        "category_b_revenue": revenue_b,
        "revenue_difference": difference,
        "percentage_change_relative_to_category_b": percentage_change,
        "revenue_ratio": revenue_ratio,
        "formula": (
            "(Category A revenue - Category B revenue) "
            "/ Category B revenue * 100"
        )
    }



def get_reorder_recommendations(inventory, branch=None):
    """
    Recommend replenishment quantities using
    existing inventory reorder thresholds.

    Unknown stock quantities are excluded.
    """

    recommendations = get_reorder_suggestions(
        inventory,
        branch=branch
    )

    if recommendations.empty:
        return recommendations

    columns = [
        "product_id",
        "product_name",
        "category",
        "branch",
        "stock_qty",
        "reorder_level",
        "suggested_reorder_qty"
    ]

    return (
        recommendations[columns]
        .sort_values(
            ["branch", "suggested_reorder_qty"],
            ascending=[True, False]
        )
        .reset_index(drop=True)
    )


def get_slow_moving_inventory(
    sales,
    inventory,
    start_date,
    end_date,
    max_units_sold=5,
    branch=None
):
    """
    Identify products selling at or below a
    configurable net-unit threshold.

    Only products with known stock and price
    contribute to capital calculations.
    """

    if max_units_sold < 0:
        raise ValueError(
            "max_units_sold cannot be negative."
        )

    products = get_slow_moving_products(
        sales,
        inventory,
        start_date,
        end_date,
        branch=branch
    )

    slow = products[
        products["units_sold"] <= max_units_sold
    ].copy()

    slow["capital_value_known"] = (
        slow["stock_qty"].notna()
        & slow["price"].notna()
    )

    return slow.reset_index(drop=True)


def calculate_slow_moving_capital(
    sales,
    inventory,
    start_date,
    end_date,
    max_units_sold=5,
    branch=None
):
    """
    Calculate the known inventory value held
    in slow-moving products.
    """

    slow = get_slow_moving_inventory(
        sales,
        inventory,
        start_date,
        end_date,
        max_units_sold,
        branch
    )

    known = slow[
        slow["capital_value_known"]
    ]

    unknown = slow[
        ~slow["capital_value_known"]
    ]

    return {
        "slow_moving_product_records": len(slow),
        "known_stock_value": float(
            known["stock_value"].sum()
        ),
        "records_with_unknown_value": len(unknown),
        "threshold_units_sold": max_units_sold,
        "period_start": str(start_date),
        "period_end": str(end_date)
    }


def get_branch_performance_insights(
    sales,
    inventory,
    start_date,
    end_date
):
    """
    Compare branches using actual sales metrics.
    """

    comparison = compare_branch_sales(
        sales,
        inventory,
        start_date,
        end_date
    )

    if comparison.empty:
        return {
            "status": "no_data",
            "message": "No branch sales found."
        }

    comparison = comparison.copy()

    total_revenue = comparison["revenue"].sum()

    comparison["revenue_share_percent"] = (
        comparison["revenue"] / total_revenue * 100
        if total_revenue else 0
    )

    return {
        "period_start": str(start_date),
        "period_end": str(end_date),
        "total_revenue": float(total_revenue),
        "branches": comparison.to_dict(
            orient="records"
        )
    }


def generate_business_recommendations(
    inventory,
    sales,
    start_date,
    end_date
):
    """
    Generate rule-based business recommendations.

    These are operational suggestions, not
    AI-generated predictions.
    """

    recommendations = []

    reorder = get_reorder_recommendations(inventory)

    if not reorder.empty:
        recommendations.append({
            "type": "inventory",
            "priority": "high",
            "title": "Replenish low-stock products",
            "details": (
                f"{len(reorder)} product-branch records "
                "require replenishment."
            )
        })

    slow = get_slow_moving_inventory(
        sales,
        inventory,
        start_date,
        end_date,
        max_units_sold=5
    )

    if not slow.empty:
        known_value = slow.loc[
            slow["capital_value_known"],
            "stock_value"
        ].sum()

        recommendations.append({
            "type": "sales",
            "priority": "medium",
            "title": "Review slow-moving inventory",
            "details": (
                f"{len(slow)} product-branch records "
                "sold five or fewer net units. "
                f"Known stock value: ₹{known_value:,.2f}."
            )
        })

    if not recommendations:
        recommendations.append({
            "type": "general",
            "priority": "low",
            "title": "No immediate issues detected",
            "details": (
                "No low-stock or slow-moving "
                "inventory alerts were found."
            )
        })

    return recommendations


if __name__ == "__main__":

    from utils.data_cleaning import (
        clean_inventory,
        clean_sales
    )

    raw_inventory = pd.read_csv("data/inventory.csv")
    raw_sales = pd.read_csv("data/sales.csv")

    inventory = clean_inventory(raw_inventory)
    sales = clean_sales(raw_sales, inventory)

    START = "2026-10-01"
    END = "2026-10-31"

    print("\n========== BUSINESS INTELLIGENCE ==========")

    print("\n1. Reorder recommendations:")
    print(
        get_reorder_recommendations(
            inventory
        ).to_string(index=False)
    )

    print("\n2. Slow-moving inventory:")
    print(
        get_slow_moving_inventory(
            sales, inventory, START, END
        )[
            ["product_id", "branch", "units_sold",
             "stock_qty", "stock_value"]
        ].to_string(index=False)
    )

    print("\n3. Capital tied in slow-moving inventory:")
    print(
        calculate_slow_moving_capital(
            sales, inventory, START, END
        )
    )

    print("\n4. Branch performance:")
    print(
        get_branch_performance_insights(
            sales, inventory, START, END
        )
    )

    print("\n5. Business recommendations:")
    for recommendation in generate_business_recommendations(
        inventory, sales, START, END
    ):
        print(recommendation)

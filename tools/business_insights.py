
import pandas as pd

from tools.inventory_tools import get_reorder_suggestions
from tools.sales_tools import (
    get_slow_moving_products,
    compare_branch_sales
)


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

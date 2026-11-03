
import math
from datetime import date, datetime

import pandas as pd

from agents.data_loader import load_data
from tools.inventory_tools import (
    get_inventory,
    get_inventory_summary,
    get_low_stock,
    search_products,
)
from tools.sales_tools import (
    calculate_revenue,
    compare_branch_sales,
    get_best_selling_products,
    get_category_sales,
    get_sales_by_period,
    get_slow_moving_products,
)
from tools.business_insights import (
    calculate_slow_moving_capital,
    generate_business_recommendations,
    get_branch_performance_insights,
    get_reorder_recommendations,
    get_slow_moving_inventory,
    get_category_revenue_metrics,
    compare_category_revenue,
)


# Load the cleaned datasets once and reuse them.
inventory, sales = load_data()


def to_jsonable(value):
    """Convert Python and Pandas results into JSON-compatible values."""

    if isinstance(value, pd.DataFrame):
        return to_jsonable(value.to_dict(orient="records"))

    if isinstance(value, pd.Series):
        return to_jsonable(value.to_dict())

    if isinstance(value, dict):
        return {
            str(key): to_jsonable(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]

    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()

    if hasattr(value, "item"):
        return to_jsonable(value.item())

    if isinstance(value, float) and not math.isfinite(value):
        return None

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


# --------------------------------------------------
# Claude tool definitions
# --------------------------------------------------

def optional_branch():
    return {
        "type": "string",
        "enum": ["Branch 1", "Branch 2"],
        "description": "Optional branch filter."
    }


def date_properties():
    return {
        "start_date": {
            "type": "string",
            "description": "Start date in YYYY-MM-DD format."
        },
        "end_date": {
            "type": "string",
            "description": "End date in YYYY-MM-DD format."
        }
    }


def date_tool_schema(extra_properties=None, required=None):
    properties = date_properties()

    if extra_properties:
        properties.update(extra_properties)

    return {
        "type": "object",
        "properties": properties,
        "required": required or ["start_date", "end_date"]
    }


TOOL_DEFINITIONS = [
    {
        "name": "get_inventory",
        "description": "Retrieve inventory records, optionally filtered by branch.",
        "input_schema": {
            "type": "object",
            "properties": {"branch": optional_branch()},
            "required": []
        }
    },
    {
        "name": "get_inventory_summary",
        "description": "Get an overall inventory summary including stock and inventory value.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_low_stock",
        "description": "Find products whose stock is at or below their reorder level.",
        "input_schema": {
            "type": "object",
            "properties": {"branch": optional_branch()},
            "required": []
        }
    },
    {
        "name": "get_reorder_recommendations",
        "description": "Get suggested reorder quantities for products in each branch.",
        "input_schema": {
            "type": "object",
            "properties": {"branch": optional_branch()},
            "required": []
        }
    },
    {
        "name": "search_products",
        "description": "Search inventory by category and/or minimum and maximum price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Product category to search for."
                },
                "min_price": {
                    "type": "number",
                    "description": "Optional minimum price."
                },
                "max_price": {
                    "type": "number",
                    "description": "Optional maximum price."
                }
            },
            "required": []
        }
    },
    {
        "name": "calculate_revenue",
        "description": "Calculate revenue and transaction counts for a date range, optionally by branch.",
        "input_schema": date_tool_schema({
            "branch": optional_branch()
        })
    },
    {
        "name": "compare_branch_sales",
        "description": "Compare sales performance between branches, optionally for a category.",
        "input_schema": date_tool_schema({
            "category": {
                "type": "string",
                "description": "Optional category filter, such as Saree."
            }
        })
    },
    {
        "name": "get_best_selling_products",
        "description": "Find the best-selling products by units sold in a date range.",
        "input_schema": date_tool_schema({
            "top_n": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "description": "Number of products to return. Defaults to 5."
            },
            "branch": optional_branch()
        })
    },
    {
        "name": "get_category_sales",
        "description": "Calculate sales performance by product category.",
        "input_schema": date_tool_schema({
            "branch": optional_branch()
        })
    },
     
    {
        "name": "get_category_revenue_metrics",
        "description": (
            "Calculate revenue, units sold, transactions and "
            "revenue share for every product category."
        ),
        "input_schema": date_tool_schema({
            "branch": optional_branch()
        })
    },
    {
        "name": "compare_category_revenue",
        "description": (
            "Compare revenue between two exact product categories. "
            "Returns the revenue difference, percentage change "
            "relative to category B and revenue ratio. "
            "Use exact category names from the sales data."
        ),
        "input_schema": date_tool_schema(
            {
                "category_a": {
                    "type": "string",
                    "description": "First category to compare."
                },
                "category_b": {
                    "type": "string",
                    "description": "Second category to compare."
                }
            },
            required=[
                "start_date",
                "end_date",
                "category_a",
                "category_b"
            ]
        )
    },


    {
        "name": "get_sales_by_period",
        "description": "Retrieve individual sales records within a date range.",
        "input_schema": date_tool_schema({
            "branch": optional_branch()
        })
    },
    {
        "name": "get_slow_moving_products",
        "description": "Identify products with low sales in a date range.",
        "input_schema": date_tool_schema({
            "branch": optional_branch()
        })
    },
    {
        "name": "calculate_slow_moving_capital",
        "description": "Calculate the known stock value tied up in slow-moving products.",
        "input_schema": date_tool_schema({
            "max_units_sold": {
                "type": "integer",
                "minimum": 0,
                "description": "Maximum units sold to classify an item as slow-moving. Defaults to 5."
            },
            "branch": optional_branch()
        })
    },
    {
        "name": "get_slow_moving_inventory",
        "description": "Get detailed inventory records for slow-moving products.",
        "input_schema": date_tool_schema({
            "max_units_sold": {
                "type": "integer",
                "minimum": 0,
                "description": "Maximum units sold. Defaults to 5."
            },
            "branch": optional_branch()
        })
    },
    {
        "name": "get_branch_performance_insights",
        "description": "Get branch-level revenue, units sold and revenue share.",
        "input_schema": date_tool_schema()
    },
    {
        "name": "generate_business_recommendations",
        "description": "Generate combined inventory and sales recommendations for a date range.",
        "input_schema": date_tool_schema()
    }
]


# --------------------------------------------------
# Tool execution
# --------------------------------------------------

def execute_tool(tool_name, tool_input):
    """
    Execute the Python function selected by Claude.

    Returns a JSON-compatible result.
    """

    try:
        args = tool_input or {}

        if tool_name == "get_inventory":
            result = get_inventory(inventory, **args)

        elif tool_name == "get_inventory_summary":
            result = get_inventory_summary(inventory)

        elif tool_name == "get_low_stock":
            result = get_low_stock(inventory, **args)

        elif tool_name == "get_reorder_recommendations":
            result = get_reorder_recommendations(inventory, **args)

        elif tool_name == "search_products":
            result = search_products(inventory, **args)

        elif tool_name == "calculate_revenue":
            result = calculate_revenue(sales, **args)

        elif tool_name == "compare_branch_sales":
            result = compare_branch_sales(
                sales, inventory, **args
            )

        elif tool_name == "get_best_selling_products":
            result = get_best_selling_products(
                sales, inventory, **args
            )

        elif tool_name == "get_category_sales":
            result = get_category_sales(
                sales, inventory, **args
            )

        elif tool_name == "get_category_revenue_metrics":
            result = get_category_revenue_metrics(
                sales, inventory, **args
            )

        elif tool_name == "compare_category_revenue":
            result = compare_category_revenue(
                sales, inventory, **args
            )

        elif tool_name == "get_sales_by_period":
            result = get_sales_by_period(sales, **args)

        elif tool_name == "get_slow_moving_products":
            result = get_slow_moving_products(
                sales, inventory, **args
            )

        elif tool_name == "calculate_slow_moving_capital":
            result = calculate_slow_moving_capital(
                sales, inventory, **args
            )

        elif tool_name == "get_slow_moving_inventory":
            result = get_slow_moving_inventory(
                sales, inventory, **args
            )

        elif tool_name == "get_branch_performance_insights":
            result = get_branch_performance_insights(
                sales, inventory, **args
            )

        elif tool_name == "generate_business_recommendations":
            result = generate_business_recommendations(
                inventory, sales, **args
            )

        else:
            return {
                "error": f"Unknown tool: {tool_name}"
            }

        return to_jsonable(result)

    except Exception as error:
        return {
            "error": str(error),
            "tool": tool_name
        }


if __name__ == "__main__":
    print("TOOL REGISTRY TEST")
    print("-" * 40)

    print("Registered tools:", len(TOOL_DEFINITIONS))

    for tool in TOOL_DEFINITIONS:
        print("-", tool["name"])

    print("\nTesting inventory summary:")

    result = execute_tool("get_inventory_summary", {})

    print(result)

    print("\nTesting October revenue:")

    result = execute_tool(
        "calculate_revenue",
        {
            "start_date": "2026-10-01",
            "end_date": "2026-10-31"
        }
    )

    print(result)

    print("\nTool registry test completed!")

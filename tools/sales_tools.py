
import pandas as pd


def _filter_sales(
    sales,
    start_date,
    end_date,
    branch=None
):
    """Filter cleaned sales by date and optional branch."""

    df = sales.copy()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    if start > end:
        raise ValueError("Start date cannot be after end date.")

    df = df[
        (df["date"] >= start)
        & (df["date"] < end + pd.Timedelta(days=1))
    ]

    if branch:
        df = df[
            df["branch"].str.casefold()
            == branch.strip().casefold()
        ]

    return df.copy()


def _add_revenue(df):
    """Calculate net revenue after discounts and returns."""

    result = df.copy()

    result["discount"] = pd.to_numeric(
        result["discount"],
        errors="coerce"
    )

    result["unit_price"] = pd.to_numeric(
        result["unit_price"],
        errors="coerce"
    )

    result["quantity"] = pd.to_numeric(
        result["quantity"],
        errors="coerce"
    )

    # Discounts are stored as fractions:
    # 5% = 0.05, 10% = 0.10.

    result["net_revenue"] = (
        result["quantity"]
        * result["unit_price"]
        * (1 - result["discount"])
    )

    return result


def get_sales_by_period(
    sales,
    start_date,
    end_date,
    branch=None
):
    """Retrieve transactions within a date range."""

    return _filter_sales(
        sales,
        start_date,
        end_date,
        branch
    ).reset_index(drop=True)


def get_best_selling_products(
    sales,
    inventory,
    start_date,
    end_date,
    top_n=5,
    branch=None
):
    """Rank products by net quantity sold."""

    if top_n < 1:
        raise ValueError("top_n must be at least 1.")

    df = get_sales_by_period(
        sales,
        start_date,
        end_date,
        branch
    )

    df = _add_revenue(df)

    result = (
        df.groupby("product_id")
        .agg(
            units_sold=("quantity", "sum"),
            revenue=("net_revenue", "sum"),
            transactions=("order_id", "nunique")
        )
        .reset_index()
    )

    # Attach product information without duplicating
    # products that appear in multiple branches.

    product_info = (
        inventory[
            ["product_id", "product_name", "category"]
        ]
        .drop_duplicates("product_id")
    )

    result = result.merge(
        product_info,
        on="product_id",
        how="left"
    )

    result["product_name"] = result[
        "product_name"
    ].fillna("Unknown product")

    return (
        result.sort_values(
            ["units_sold", "revenue"],
            ascending=[False, False]
        )
        .head(top_n)
        .reset_index(drop=True)
    )


def calculate_revenue(
    sales,
    start_date,
    end_date,
    branch=None
):
    """Calculate net revenue after discounts and returns."""

    df = get_sales_by_period(
        sales,
        start_date,
        end_date,
        branch
    )

    df = _add_revenue(df)

    known = df["net_revenue"].notna()

    return {
        "total_transactions": len(df),
        "transactions_included": int(known.sum()),
        "transactions_excluded": int((~known).sum()),
        "total_revenue": float(
            df.loc[known, "net_revenue"].sum()
        )
    }


def get_category_sales(
    sales,
    inventory,
    start_date,
    end_date,
    branch=None
):
    """Calculate revenue and units sold by category."""

    df = get_sales_by_period(
        sales,
        start_date,
        end_date,
        branch
    )

    df = _add_revenue(df)

    product_info = (
        inventory[
            ["product_id", "category"]
        ]
        .drop_duplicates("product_id")
    )

    df = df.merge(
        product_info,
        on="product_id",
        how="left"
    )

    df["category"] = df["category"].fillna(
        "Unknown - not in inventory"
    )

    result = (
        df.groupby("category")
        .agg(
            units_sold=("quantity", "sum"),
            revenue=("net_revenue", "sum"),
            transactions=("order_id", "nunique")
        )
        .reset_index()
    )

    return result.sort_values(
        "revenue",
        ascending=False
    ).reset_index(drop=True)


def compare_branch_sales(
    sales,
    inventory,
    start_date,
    end_date,
    category=None
):
    """Compare sales performance across branches."""

    df = get_sales_by_period(
        sales,
        start_date,
        end_date
    )

    if category:
        product_info = inventory[
            ["product_id", "category"]
        ].drop_duplicates("product_id")

        df = df.merge(
            product_info,
            on="product_id",
            how="left"
        )

        df = df[
            df["category"].str.casefold()
            == category.strip().casefold()
        ]

    df = _add_revenue(df)

    result = (
        df.groupby("branch")
        .agg(
            units_sold=("quantity", "sum"),
            revenue=("net_revenue", "sum"),
            transactions=("order_id", "nunique")
        )
        .reset_index()
    )

    return result.sort_values(
        "revenue",
        ascending=False
    ).reset_index(drop=True)


def get_slow_moving_products(
    sales,
    inventory,
    start_date,
    end_date,
    branch=None
):
    """
    Identify products with no or low net sales.

    Includes inventory stock value to estimate
    capital tied up in slow-moving products.
    """

    stock = inventory.copy()

    if branch:
        stock = stock[
            stock["branch"].str.casefold()
            == branch.strip().casefold()
        ]

    period_sales = get_sales_by_period(
        sales,
        start_date,
        end_date,
        branch
    )

    period_sales = _add_revenue(period_sales)

    sales_summary = (
        period_sales.groupby(
            ["product_id", "branch"]
        )
        .agg(
            units_sold=("quantity", "sum"),
            sales_revenue=("net_revenue", "sum")
        )
        .reset_index()
    )

    result = stock.merge(
        sales_summary,
        on=["product_id", "branch"],
        how="left"
    )

    result["units_sold"] = result["units_sold"].fillna(0)
    result["sales_revenue"] = result["sales_revenue"].fillna(0)

    result["stock_value"] = (
        result["stock_qty"] * result["price"]
    )

    return result.sort_values(
        ["units_sold", "stock_value"],
        ascending=[True, False]
    ).reset_index(drop=True)


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

    print("\n========== SALES ANALYTICS TEST ==========")

    print("\n1. October sales:")
    print(
        get_sales_by_period(
            sales, START, END
        ).head()
    )

    print("\n2. Best-selling products:")
    print(
        get_best_selling_products(
            sales, inventory, START, END
        ).to_string(index=False)
    )

    print("\n3. October revenue:")
    print(
        calculate_revenue(
            sales, START, END
        )
    )

    print("\n4. Category sales:")
    print(
        get_category_sales(
            sales, inventory, START, END
        ).to_string(index=False)
    )

    print("\n5. Branch comparison:")
    print(
        compare_branch_sales(
            sales, inventory, START, END
        ).to_string(index=False)
    )

    print("\n6. Slow-moving products:")
    print(
        get_slow_moving_products(
            sales, inventory, START, END
        )[
            [
                "product_id",
                "branch",
                "stock_qty",
                "units_sold",
                "stock_value"
            ]
        ].head(15).to_string(index=False)
    )

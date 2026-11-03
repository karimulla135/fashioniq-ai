
import pandas as pd


def get_inventory(inventory, branch=None):
    """
    Retrieve inventory for all branches or a specific branch.
    """

    df = inventory.copy()

    if branch is not None:
        df = df[
            df["branch"].str.casefold()
            == branch.strip().casefold()
        ]

    return df.reset_index(drop=True)


def get_low_stock(inventory, branch=None):
    """
    Find products whose stock is at or below reorder level.

    Unknown stock quantities are excluded because
    they cannot be reliably classified.
    """

    df = inventory.copy()

    if branch is not None:
        df = df[
            df["branch"].str.casefold()
            == branch.strip().casefold()
        ]

    known_stock = df[
        df["stock_qty"].notna()
        & df["reorder_level"].notna()
    ].copy()

    low_stock = known_stock[
        known_stock["stock_qty"]
        <= known_stock["reorder_level"]
    ]

    return low_stock.reset_index(drop=True)


def search_products(
    inventory,
    category=None,
    min_price=None,
    max_price=None
):
    """
    Search products by category and price range.
    """

    df = inventory.copy()

    if category:
        df = df[
            df["category"].str.casefold()
            == category.strip().casefold()
        ]

    if min_price is not None:
        df = df[df["price"] >= min_price]

    if max_price is not None:
        df = df[df["price"] <= max_price]

    return df.reset_index(drop=True)


def get_inventory_summary(inventory):
    """
    Generate an overall inventory summary.
    """

    total_records = len(inventory)

    unique_products = inventory["product_id"].nunique()

    total_known_stock = inventory["stock_qty"].sum(
        min_count=1
    )

    missing_stock_records = int(
        inventory["stock_qty"].isna().sum()
    )

    # Only value records with known stock and price.
    valued_records = inventory[
        inventory["stock_qty"].notna()
        & inventory["price"].notna()
    ]

    inventory_value = (
        valued_records["stock_qty"]
        * valued_records["price"]
    ).sum()

    return {
        "total_inventory_records": total_records,
        "unique_products": int(unique_products),
        "total_known_stock": (
            None if pd.isna(total_known_stock)
            else float(total_known_stock)
        ),
        "missing_stock_records": missing_stock_records,
        "inventory_value": float(inventory_value),
        "branch_count": int(inventory["branch"].nunique())
    }


def get_reorder_suggestions(inventory, branch=None):
    """
    Calculate quantities required to reach reorder levels.

    This is a basic replenishment calculation, not
    a demand forecast.
    """

    low_stock = get_low_stock(inventory, branch)

    low_stock = low_stock.copy()

    low_stock["suggested_reorder_qty"] = (
        low_stock["reorder_level"]
        - low_stock["stock_qty"]
    ).clip(lower=0)

    low_stock = low_stock[
    low_stock["suggested_reorder_qty"] > 0
]

    return low_stock.reset_index(drop=True)


if __name__ == "__main__":

    from utils.data_cleaning import clean_inventory

    raw_inventory = pd.read_csv("data/inventory.csv")

    inventory = clean_inventory(raw_inventory)

    print("\n========== INVENTORY TOOLS TEST ==========")

    print("\n1. Overall inventory:")
    print(get_inventory(inventory).head())

    print("\n2. Branch 1 inventory:")
    print(get_inventory(inventory, "Branch 1").head())

    print("\n3. Low stock products:")
    print(get_low_stock(inventory).to_string(index=False))

    print("\n4. Saree search:")
    print(
        search_products(
            inventory,
            category="Saree"
        ).to_string(index=False)
    )

    print("\n5. Inventory summary:")
    print(get_inventory_summary(inventory))

    print("\n6. Reorder suggestions:")
    print(
        get_reorder_suggestions(inventory)[
            [
                "product_id",
                "branch",
                "stock_qty",
                "reorder_level",
                "suggested_reorder_qty"
            ]
        ].to_string(index=False)
    )

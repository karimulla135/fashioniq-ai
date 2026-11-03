
from functools import lru_cache
from pathlib import Path

import pandas as pd

from utils.data_cleaning import clean_inventory, clean_sales


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INVENTORY_FILE = DATA_DIR / "inventory.csv"
SALES_FILE = DATA_DIR / "sales.csv"


@lru_cache(maxsize=1)
def load_data():
    """
    Load and clean inventory and sales datasets.

    Data is loaded only once and reused across tool calls.
    """

    # Check that both datasets exist
    if not INVENTORY_FILE.exists():
        raise FileNotFoundError(
            f"Inventory dataset not found: {INVENTORY_FILE}"
        )

    if not SALES_FILE.exists():
        raise FileNotFoundError(
            f"Sales dataset not found: {SALES_FILE}"
        )

    # Read original CSV files
    raw_inventory = pd.read_csv(INVENTORY_FILE, low_memory=False)
    raw_sales = pd.read_csv(SALES_FILE, low_memory=False)

    # Clean inventory first
    inventory = clean_inventory(raw_inventory)

    # Clean sales using cleaned inventory
    sales = clean_sales(raw_sales, inventory)

    return inventory, sales


if __name__ == "__main__":
    inventory, sales = load_data()

    print("\nDATA LOADER TEST")
    print("-" * 40)

    print(f"Inventory records: {len(inventory)}")
    print(f"Sales records: {len(sales)}")

    print("\nInventory columns:")
    print(inventory.columns.tolist())

    print("\nSales columns:")
    print(sales.columns.tolist())

    print("\nFirst 3 inventory records:")
    print(inventory.head(3).to_string(index=False))

    print("\nFirst 3 sales records:")
    print(sales.head(3).to_string(index=False))

    print("\nData loading and cleaning successful!")

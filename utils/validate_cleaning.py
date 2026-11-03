
import pandas as pd

from data_cleaning import clean_inventory, clean_sales


# Load original datasets
raw_inventory = pd.read_csv("data/inventory.csv")
raw_sales = pd.read_csv("data/sales.csv")

# Clean datasets
inventory = clean_inventory(raw_inventory)
sales = clean_sales(df=raw_sales, inventory=inventory)


print("\n========== STOCK VALIDATION ==========")

# Find all stock values that became missing
invalid_stock = inventory[inventory["stock_qty"].isna()].copy()

# Show original values alongside product details
invalid_stock["original_stock_qty"] = raw_inventory.loc[
    invalid_stock.index, "stock_qty"
]

print("\nRecords with missing/invalid stock:")
print(
    invalid_stock[
        ["product_id", "branch", "original_stock_qty", "stock_qty"]
    ].to_string(index=False)
)

print("\nOriginal missing stock count:")
print(raw_inventory["stock_qty"].isna().sum())

print("\nCleaned missing stock count:")
print(inventory["stock_qty"].isna().sum())


print("\n========== UNKNOWN PRODUCT VALIDATION ==========")

unknown_sales = sales[
    sales["product_missing_from_inventory"]
]

print("\nDistinct unknown product IDs:")
print(unknown_sales["product_id"].unique())

print("\nUnknown product transaction count:")
print(len(unknown_sales))

print("\nTransactions per unknown product:")
print(unknown_sales.groupby("product_id").size())


print("\n========== PRICE RECOVERY VALIDATION ==========")

print("Prices recovered:", sales["price_imputed"].sum())

print(
    "Remaining missing prices:",
    sales["unit_price"].isna().sum()
)

print("\nValidation investigation completed!")

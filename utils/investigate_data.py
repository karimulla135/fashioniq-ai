
import pandas as pd

# Load original datasets
inventory = pd.read_csv("data/inventory.csv")
sales = pd.read_csv("data/sales.csv")


def investigate_inventory():

    print("\n========== INVENTORY INVESTIGATION ==========")

    # 1. Missing stock
    print("\n1. Products with missing stock:")
    print(inventory[inventory["stock_qty"].isna()].to_string(index=False))

    # 2. Different category names
    print("\n2. Unique categories:")
    print(sorted(inventory["category"].dropna().unique()))

    # 3. Different price formats
    print("\n3. Sample inventory prices:")
    print(inventory["price"].unique()[:15])

    # 4. Product IDs
    print("\n4. Product IDs:")
    print("Total inventory records:", len(inventory))
    print("Unique product IDs:",
          inventory["product_id"].str.strip().str.upper().nunique())


def investigate_sales():

    print("\n========== SALES INVESTIGATION ==========")

    # 1. Missing prices
    missing_prices = sales[sales["unit_price"].isna()]

    print("\n1. Missing sales prices:")
    print("Total:", len(missing_prices))

    print("\nMissing prices by branch:")
    print(missing_prices.groupby("branch").size())

    # 2. Negative quantities / returns
    returns = sales[sales["quantity"] < 0]

    print("\n2. Return records:")
    print(returns.to_string(index=False))

    # 3. Products missing from inventory
    inventory_ids = set(
        inventory["product_id"].str.strip().str.upper()
    )

    sales_ids = set(
        sales["product_id"].str.strip().str.upper()
    )

    missing_products = sales_ids - inventory_ids

    print("\n3. Products sold but absent from inventory:")
    print(missing_products)

    # 4. Product ID inconsistencies
    print("\n4. Raw sales product IDs with mixed casing:")
    print(
        sales[
            sales["product_id"] !=
            sales["product_id"].str.upper()
        ]["product_id"].unique()
    )

    # 5. Discount formats
    print("\n5. Discount values:")
    print(sales["discount"].value_counts(dropna=False))

    # 6. Date formats
    print("\n6. Sample sales dates:")
    print(sales["date"].unique()[:15])


if __name__ == "__main__":

    investigate_inventory()
    investigate_sales()

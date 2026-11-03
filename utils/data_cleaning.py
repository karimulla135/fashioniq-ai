
import pandas as pd
import re


def parse_price(value):
    """Convert different INR price formats into numbers."""

    if pd.isna(value):
        return float("nan")

    cleaned = str(value).strip()

    cleaned = re.sub(
        r"(?i)\brs\.?\s*|₹|/-",
        "",
        cleaned
    )

    cleaned = cleaned.replace(",", "").strip()

    try:
        return float(cleaned)
    except ValueError:
        return float("nan")


def parse_discount(value):
    """Convert discount values into decimal rates."""

    if pd.isna(value):
        return float("nan")

    cleaned = str(value).strip()

    if cleaned.endswith("%"):
        return float(cleaned[:-1].strip()) / 100

    return float(cleaned)


def parse_stock_qty(value):
    """Normalize stock quantities while preserving unknown values."""

    if pd.isna(value):
        return float("nan")

    cleaned = str(value).strip().lower()

    if cleaned == "out of stock":
        return 0

    cleaned = re.sub(
        r"\s*(pc|pcs|pieces?)\s*$",
        "",
        cleaned
    )

    try:
        return float(cleaned)
    except ValueError:
        return float("nan")


def parse_mixed_date(value):
    """Safely parse ISO and day-first date formats."""

    if pd.isna(value):
        return pd.NaT

    value = str(value).strip()

    try:
        # ISO format: YYYY-MM-DD
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return pd.to_datetime(
                value,
                format="%Y-%m-%d",
                errors="coerce"
            )

        # Other formats: DD-MM-YYYY or DD/MM/YYYY
        return pd.to_datetime(
            value,
            dayfirst=True,
            errors="coerce"
        )

    except (ValueError, TypeError):
        return pd.NaT



def clean_inventory(df):

    df = df.copy()

    # Normalize product IDs
    df["product_id"] = (
        df["product_id"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # Normalize text fields
    for column in [
        "product_name",
        "category",
        "fabric",
        "colour",
        "branch"
    ]:
        df[column] = df[column].astype("string").str.strip()

    # Standardize category names
    df["category"] = df["category"].str.title()

    # Convert prices
    df["price"] = df["price"].apply(parse_price)

    # Convert numerical columns
    df["stock_qty"] = df["stock_qty"].apply(parse_stock_qty)

    df["reorder_level"] = pd.to_numeric(
        df["reorder_level"], errors="coerce"
    )

    # Parse restock dates
    df["last_restocked"] = df["last_restocked"].apply(
    parse_mixed_date
)

    # Preserve missing stock as unknown
    df["stock_missing"] = df["stock_qty"].isna()
    df["stock_is_zero"] = df["stock_qty"].eq(0)

    return df


def clean_sales(df, inventory):

    df = df.copy()

    # Normalize IDs and text
    for column in ["product_id", "branch"]:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    df["product_id"] = df["product_id"].str.upper()

    # Parse dates, including mixed formats
    df["date"] = df["date"].apply(parse_mixed_date)

    # Convert numerical values
    df["quantity"] = pd.to_numeric(
        df["quantity"], errors="coerce"
    )

    df["unit_price"] = pd.to_numeric(
        df["unit_price"], errors="coerce"
    )

    df["discount"] = df["discount"].apply(
        parse_discount
    )

    # Track missing prices before recovery
    df["price_imputed"] = df["unit_price"].isna()

    # Build branch-specific inventory price lookup
    price_lookup = inventory[
        ["product_id", "branch", "price"]
    ].drop_duplicates(
        ["product_id", "branch"]
    )

    price_lookup = price_lookup.rename(
        columns={"price": "catalogue_price"}
    )

    df = df.merge(
        price_lookup,
        on=["product_id", "branch"],
        how="left",
        validate="many_to_one"
    )

    # Recover missing prices only from matched catalogue data
    recoverable = (
        df["unit_price"].isna()
        & df["catalogue_price"].notna()
    )

    df.loc[recoverable, "unit_price"] = (
        df.loc[recoverable, "catalogue_price"]
    )

    # Flag unknown products
    df["product_missing_from_inventory"] = (
        df["catalogue_price"].isna()
    )

    # Preserve returns
    df["is_return"] = df["quantity"] < 0

    return df


if __name__ == "__main__":

    raw_inventory = pd.read_csv("data/inventory.csv")
    raw_sales = pd.read_csv("data/sales.csv")

    inventory = clean_inventory(raw_inventory)
    sales = clean_sales(raw_sales, inventory)

    print("INVENTORY CLEANING")
    print("Records:", len(inventory))
    print("Missing stock:", inventory["stock_missing"].sum())
    print("Invalid prices:", inventory["price"].isna().sum())

    print("\nSALES CLEANING")
    print("Records:", len(sales))
    print("Recovered prices:", sales["price_imputed"].sum())
    print("Unresolved prices:", sales["unit_price"].isna().sum())
    print(
        "Unknown products:",
        sales["product_missing_from_inventory"].sum()
    )
    print("Returns:", sales["is_return"].sum())

    print("\nCleaning completed!")



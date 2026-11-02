
import pandas as pd

# Load the datasets
inventory = pd.read_csv("data/inventory.csv")
sales = pd.read_csv("data/sales.csv")


def inspect_dataset(name, df):

    print("\n" + "=" * 55)
    print(f"DATASET: {name}")
    print("=" * 55)

    # Dataset dimensions
    print("\n1. Dataset Shape:")
    print(df.shape)

    # Column information
    print("\n2. Column Names:")
    print(df.columns.tolist())

    # Data types
    print("\n3. Data Types:")
    print(df.dtypes)

    # Missing values
    print("\n4. Missing Values:")
    print(df.isnull().sum())

    # Duplicate records
    print("\n5. Duplicate Rows:")
    print(df.duplicated().sum())

    # Preview
    print("\n6. First Five Records:")
    print(df.head())


# Run inspection
inspect_dataset("INVENTORY", inventory)
inspect_dataset("SALES", sales)

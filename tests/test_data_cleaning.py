
import pandas as pd
import pytest

from utils.data_cleaning import (
    parse_price,
    parse_discount,
    parse_stock_qty,
    clean_inventory,
    clean_sales
)


# ==========================================
# 1. PRICE CONVERSION TESTS
# ==========================================

@pytest.mark.parametrize(
    "value, expected",
    [
        ("4299", 4299.0),
        ("₹4,299", 4299.0),
        ("Rs. 2899", 2899.0),
        ("6499/-", 6499.0),
        ("₹6,499", 6499.0),
    ]
)
def test_parse_price(value, expected):
    assert parse_price(value) == expected


def test_parse_missing_price():
    assert pd.isna(parse_price(None))


# ==========================================
# 2. DISCOUNT CONVERSION TESTS
# ==========================================

@pytest.mark.parametrize(
    "value, expected",
    [
        ("5%", 0.05),
        ("10%", 0.10),
        ("15%", 0.15),
        ("0", 0.0),
    ]
)
def test_parse_discount(value, expected):
    assert parse_discount(value) == expected


# ==========================================
# 3. STOCK QUANTITY TESTS
# ==========================================

@pytest.mark.parametrize(
    "value, expected",
    [
        ("1 pc", 1),
        ("5 pieces", 5),
        ("out of stock", 0),
        ("10", 10),
    ]
)
def test_parse_stock_qty(value, expected):
    assert parse_stock_qty(value) == expected


def test_missing_stock_remains_missing():
    assert pd.isna(parse_stock_qty(None))


# ==========================================
# 4. INVENTORY CLEANING TEST
# ==========================================

def test_clean_inventory():

    raw_inventory = pd.DataFrame({
        "product_id": ["tz-101", "TZ-102", "TZ-103"],
        "product_name": ["Product A", "Product B", "Product C"],
        "category": ["saree", "SAREE", "lehenga"],
        "fabric": ["Silk", "Cotton", "Georgette"],
        "colour": ["Red", "Blue", "Green"],
        "price": ["₹4,299", "Rs. 2899", "3999/-"],
        "branch": ["Branch 1", "Branch 1", "Branch 2"],
        "stock_qty": ["1 pc", "out of stock", None],
        "reorder_level": [5, 3, 4],
        "last_restocked": [
            "2026-10-01",
            "2026-09-28",
            "2026-09-25"
        ]
    })

    cleaned = clean_inventory(raw_inventory)

    assert cleaned["product_id"].tolist() == [
        "TZ-101", "TZ-102", "TZ-103"
    ]

    assert cleaned["price"].tolist() == [
        4299.0, 2899.0, 3999.0
    ]

    assert cleaned["stock_qty"].iloc[0] == 1
    assert cleaned["stock_qty"].iloc[1] == 0

    assert pd.isna(cleaned["stock_qty"].iloc[2])

    assert cleaned["stock_missing"].tolist() == [
        False, False, True
    ]

    assert cleaned["category"].tolist() == [
        "Saree", "Saree", "Lehenga"
    ]


# ==========================================
# 5. SALES CLEANING TEST
# ==========================================

def test_clean_sales():

    inventory = clean_inventory(pd.DataFrame({
        "product_id": ["TZ-101"],
        "product_name": ["Test Saree"],
        "category": ["Saree"],
        "fabric": ["Silk"],
        "colour": ["Red"],
        "price": ["4299"],
        "branch": ["Branch 1"],
        "stock_qty": ["5"],
        "reorder_level": [2],
        "last_restocked": ["2026-10-01"]
    }))

    raw_sales = pd.DataFrame({
        "order_id": ["ORD-001", "RET-001"],
        "date": ["2026-10-01", "2026-10-02"],
        "branch": ["Branch 1", "Branch 1"],
        "product_id": ["tz-101", "TZ-101"],
        "quantity": [2, -1],
        "unit_price": [None, 4299.0],
        "discount": ["5%", "0"],
        "payment_mode": ["UPI", "Cash"]
    })

    cleaned = clean_sales(raw_sales, inventory)

    assert len(cleaned) == 2

    # Missing price recovered from inventory
    assert cleaned["unit_price"].iloc[0] == 4299.0

    # Imputation tracked
    assert cleaned["price_imputed"].iloc[0]

    # Product ID normalized
    assert cleaned["product_id"].iloc[0] == "TZ-101"

    # Discount converted
    assert cleaned["discount"].iloc[0] == 0.05

    # Return preserved
    assert cleaned["quantity"].iloc[1] == -1
    assert cleaned["is_return"].iloc[1]


# ==========================================
# 6. UNKNOWN PRODUCT TEST
# ==========================================

def test_unknown_product_detection():

    inventory = clean_inventory(pd.DataFrame({
        "product_id": ["TZ-101"],
        "product_name": ["Test Saree"],
        "category": ["Saree"],
        "fabric": ["Silk"],
        "colour": ["Red"],
        "price": ["4299"],
        "branch": ["Branch 1"],
        "stock_qty": ["5"],
        "reorder_level": [2],
        "last_restocked": ["2026-10-01"]
    }))

    sales = pd.DataFrame({
        "order_id": ["ORD-002"],
        "date": ["2026-10-03"],
        "branch": ["Branch 1"],
        "product_id": ["TZ-999"],
        "quantity": [1],
        "unit_price": [None],
        "discount": ["0"],
        "payment_mode": ["UPI"]
    })

    cleaned = clean_sales(sales, inventory)

    assert cleaned["product_missing_from_inventory"].iloc[0]
    assert pd.isna(cleaned["unit_price"].iloc[0])




import pandas as pd
import pytest

from utils.data_cleaning import clean_inventory, clean_sales

from tools.sales_tools import (
    get_sales_by_period,
    get_best_selling_products,
    calculate_revenue,
    get_category_sales,
    compare_branch_sales,
    get_slow_moving_products
)


@pytest.fixture
def datasets():

    raw_inventory = pd.DataFrame({
        "product_id": ["TZ-101", "TZ-102", "TZ-103"],
        "product_name": [
            "Silk Saree",
            "Designer Lehenga",
            "Cotton Saree"
        ],
        "category": ["Saree", "Lehenga", "Saree"],
        "fabric": ["Silk", "Georgette", "Cotton"],
        "colour": ["Red", "Green", "Blue"],
        "price": ["100", "200", "50"],
        "branch": ["Branch 1", "Branch 2", "Branch 1"],
        "stock_qty": ["5", "10", "8"],
        "reorder_level": [2, 3, 4],
        "last_restocked": [
            "2026-10-01",
            "2026-10-02",
            "2026-10-03"
        ]
    })

    inventory = clean_inventory(raw_inventory)

    raw_sales = pd.DataFrame({
        "order_id": [
            "ORD-001",
            "RET-001",
            "ORD-002",
            "ORD-003",
            "ORD-004"
        ],
        "date": [
            "2026-10-01",
            "2026-10-02",
            "2026-10-03",
            "2026-10-04",
            "2026-09-30"
        ],
        "branch": [
            "Branch 1",
            "Branch 1",
            "Branch 2",
            "Branch 1",
            "Branch 1"
        ],
        "product_id": [
            "TZ-101",
            "TZ-101",
            "TZ-102",
            "TZ-999",
            "TZ-103"
        ],
        "quantity": [2, -1, 3, 1, 4],
        "unit_price": [100, 100, 200, 80, 50],
        "discount": ["10%", "0", "0", "0", "0"],
        "payment_mode": ["UPI", "Cash", "Card", "UPI", "Cash"]
    })

    sales = clean_sales(raw_sales, inventory)

    return inventory, sales


# 1. Date filtering

def test_sales_by_period(datasets):

    inventory, sales = datasets

    result = get_sales_by_period(
        sales,
        "2026-10-01",
        "2026-10-31"
    )

    assert len(result) == 4


# 2. Branch filtering

def test_sales_by_branch(datasets):

    inventory, sales = datasets

    result = get_sales_by_period(
        sales,
        "2026-10-01",
        "2026-10-31",
        branch="Branch 1"
    )

    assert len(result) == 3


# 3. Invalid date range

def test_invalid_date_range(datasets):

    inventory, sales = datasets

    with pytest.raises(ValueError):
        get_sales_by_period(
            sales,
            "2026-10-31",
            "2026-10-01"
        )


# 4. Revenue calculation

def test_revenue_calculation(datasets):

    inventory, sales = datasets

    result = calculate_revenue(
        sales,
        "2026-10-01",
        "2026-10-31"
    )

    # 180 - 100 + 600 + 80 = 760

    assert result["total_revenue"] == pytest.approx(760)
    assert result["total_transactions"] == 4
    assert result["transactions_excluded"] == 0


# 5. Best-selling products

def test_best_selling_products(datasets):

    inventory, sales = datasets

    result = get_best_selling_products(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31",
        top_n=3
    )

    assert result.iloc[0]["product_id"] == "TZ-102"
    assert result.iloc[0]["units_sold"] == 3


# 6. Category sales

def test_category_sales(datasets):

    inventory, sales = datasets

    result = get_category_sales(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31"
    )

    saree = result[
        result["category"] == "Saree"
    ]

    assert saree.iloc[0]["revenue"] == pytest.approx(80)


# 7. Branch comparison

def test_branch_comparison(datasets):

    inventory, sales = datasets

    result = compare_branch_sales(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31"
    )

    branch_1 = result[
        result["branch"] == "Branch 1"
    ]

    branch_2 = result[
        result["branch"] == "Branch 2"
    ]

    assert branch_1.iloc[0]["revenue"] == pytest.approx(160)
    assert branch_2.iloc[0]["revenue"] == pytest.approx(600)


# 8. Category-specific branch comparison

def test_saree_branch_comparison(datasets):

    inventory, sales = datasets

    result = compare_branch_sales(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31",
        category="Saree"
    )

    assert len(result) == 1
    assert result.iloc[0]["branch"] == "Branch 1"


# 9. Slow-moving products

def test_slow_moving_products(datasets):

    inventory, sales = datasets

    result = get_slow_moving_products(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31"
    )

    product = result[
        result["product_id"] == "TZ-103"
    ]

    assert product.iloc[0]["units_sold"] == 0
    assert product.iloc[0]["stock_value"] == pytest.approx(400)


# 10. Slow-moving product with no sales

def test_products_without_sales_are_included(datasets):

    inventory, sales = datasets

    result = get_slow_moving_products(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31"
    )

    assert "TZ-103" in result["product_id"].values


# 11. Top N validation

def test_invalid_top_n(datasets):

    inventory, sales = datasets

    with pytest.raises(ValueError):
        get_best_selling_products(
            sales,
            inventory,
            "2026-10-01",
            "2026-10-31",
            top_n=0
        )

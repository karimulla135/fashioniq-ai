
import pandas as pd
import pytest

from utils.data_cleaning import clean_inventory, clean_sales

from tools.business_insights import (
    get_reorder_recommendations,
    get_slow_moving_inventory,
    calculate_slow_moving_capital,
    get_branch_performance_insights,
    generate_business_recommendations,
    get_category_revenue_metrics,
    compare_category_revenue,
)


@pytest.fixture
def datasets():

    raw_inventory = pd.DataFrame({
        "product_id": [
            "TZ-101", "TZ-102", "TZ-103", "TZ-104"
        ],
        "product_name": [
            "Silk Saree",
            "Designer Lehenga",
            "Cotton Saree",
            "Banarasi Saree"
        ],
        "category": [
            "Saree", "Lehenga", "Saree", "Saree"
        ],
        "fabric": [
            "Silk", "Georgette", "Cotton", "Silk"
        ],
        "colour": [
            "Red", "Green", "Blue", "Pink"
        ],
        "price": ["100", "200", "50", "400"],
        "branch": [
            "Branch 1", "Branch 2",
            "Branch 1", "Branch 2"
        ],
        "stock_qty": ["1", "10", "0", None],
        "reorder_level": [3, 3, 2, 4],
        "last_restocked": [
            "2026-10-01",
            "2026-10-02",
            "2026-10-03",
            "2026-10-04"
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
        "payment_mode": [
            "UPI", "Cash", "Card", "UPI", "Cash"
        ]
    })

    sales = clean_sales(raw_sales, inventory)

    return inventory, sales


# 1. Reorder recommendations

def test_reorder_recommendations(datasets):

    inventory, sales = datasets

    result = get_reorder_recommendations(inventory)

    assert set(result["product_id"]) == {
        "TZ-101", "TZ-103"
    }

    assert (result["suggested_reorder_qty"] > 0).all()


# 2. Unknown stock should not be recommended

def test_unknown_stock_excluded_from_reorder(datasets):

    inventory, sales = datasets

    result = get_reorder_recommendations(inventory)

    assert "TZ-104" not in result["product_id"].values


# 3. Slow-moving inventory

def test_slow_moving_inventory(datasets):

    inventory, sales = datasets

    result = get_slow_moving_inventory(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31",
        max_units_sold=5
    )

    assert set(result["product_id"]) == {
        "TZ-101", "TZ-102", "TZ-103", "TZ-104"
    }

    assert (result["units_sold"] <= 5).all()


# 4. Capital calculation

def test_slow_moving_capital(datasets):

    inventory, sales = datasets

    result = calculate_slow_moving_capital(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31",
        max_units_sold=5
    )

    assert result["slow_moving_product_records"] == 4

    # 100 + 2000 + 0.
    # TZ-104 has unknown stock and is excluded.

    assert result["known_stock_value"] == pytest.approx(2100)

    assert result["records_with_unknown_value"] == 1


# 5. Branch performance

def test_branch_performance(datasets):

    inventory, sales = datasets

    result = get_branch_performance_insights(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31"
    )

    assert result["total_revenue"] == pytest.approx(760)

    branches = {
        item["branch"]: item
        for item in result["branches"]
    }

    assert branches["Branch 1"]["revenue"] == pytest.approx(160)

    assert branches["Branch 2"]["revenue"] == pytest.approx(600)

    total_share = sum(
        item["revenue_share_percent"]
        for item in result["branches"]
    )

    assert total_share == pytest.approx(100)


# 6. Automatic business recommendations

def test_business_recommendations(datasets):

    inventory, sales = datasets

    result = generate_business_recommendations(
        inventory,
        sales,
        "2026-10-01",
        "2026-10-31"
    )

    assert len(result) >= 2

    recommendation_types = {
        item["type"] for item in result
    }

    assert "inventory" in recommendation_types
    assert "sales" in recommendation_types


# 7. Invalid slow-moving threshold

def test_invalid_slow_moving_threshold(datasets):

    inventory, sales = datasets

    with pytest.raises(ValueError):

        get_slow_moving_inventory(
            sales,
            inventory,
            "2026-10-01",
            "2026-10-31",
            max_units_sold=-1
        )


# 8. Branch-specific reorder recommendations

def test_branch_specific_reorder(datasets):

    inventory, sales = datasets

    result = get_reorder_recommendations(
        inventory,
        branch="Branch 1"
    )

    assert set(result["product_id"]) == {
        "TZ-101", "TZ-103"
    }

    assert (result["branch"] == "Branch 1").all()


# 9. Category revenue metrics

def test_category_revenue_metrics(datasets):

    inventory, sales = datasets

    result = get_category_revenue_metrics(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31"
    )

    assert result["status"] == "success"

    assert result["total_revenue"] == pytest.approx(760)

    categories = result["categories"]

    total_share = sum(
        item["revenue_share_percent"]
        for item in categories
    )

    assert total_share == pytest.approx(100)


# 10. Exact category revenue comparison

def test_compare_category_revenue(datasets):

    inventory, sales = datasets

    result = compare_category_revenue(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31",
        "Lehenga",
        "Saree"
    )

    assert result["status"] == "success"

    assert result["category_a_revenue"] == pytest.approx(600)

    assert result["category_b_revenue"] == pytest.approx(80)

    assert result["revenue_difference"] == pytest.approx(520)

    assert (
        result["percentage_change_relative_to_category_b"]
        == pytest.approx(650)
    )

    assert result["revenue_ratio"] == pytest.approx(7.5)


# 11. Missing category handling

def test_compare_category_missing_data(datasets):

    inventory, sales = datasets

    result = compare_category_revenue(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31",
        "Saree",
        "Nonexistent Category"
    )

    assert result["status"] == "no_data"

    assert "Nonexistent Category" in result["missing_categories"]


# 12. Reject comparing the same category

def test_compare_same_category_rejected(datasets):

    inventory, sales = datasets

    with pytest.raises(ValueError):

        compare_category_revenue(
            sales,
            inventory,
            "2026-10-01",
            "2026-10-31",
            "Saree",
            "Saree"
        )


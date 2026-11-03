
import pandas as pd
import pytest

from utils.data_cleaning import clean_inventory
from tools.inventory_tools import (
    get_inventory,
    get_low_stock,
    search_products,
    get_inventory_summary,
    get_reorder_suggestions
)


@pytest.fixture
def inventory():

    raw_data = pd.DataFrame({
        "product_id": ["TZ-101", "TZ-102", "TZ-103", "TZ-104"],
        "product_name": [
            "Silk Saree",
            "Cotton Saree",
            "Designer Lehenga",
            "Banarasi Saree"
        ],
        "category": ["Saree", "Saree", "Lehenga", "Saree"],
        "fabric": ["Silk", "Cotton", "Georgette", "Silk"],
        "colour": ["Red", "Blue", "Green", "Pink"],
        "price": ["100", "200", "300", "400"],
        "branch": [
            "Branch 1", "Branch 1", "Branch 2", "Branch 2"
        ],
        "stock_qty": ["1", "5", "0", None],
        "reorder_level": [3, 3, 2, 4],
        "last_restocked": [
            "2026-10-01",
            "2026-10-02",
            "2026-10-03",
            "2026-10-04"
        ]
    })

    return clean_inventory(raw_data)


def test_get_inventory(inventory):

    result = get_inventory(inventory)

    assert len(result) == 4


def test_get_inventory_by_branch(inventory):

    result = get_inventory(inventory, "Branch 1")

    assert len(result) == 2
    assert all(result["branch"] == "Branch 1")


def test_get_low_stock(inventory):

    result = get_low_stock(inventory)

    assert set(result["product_id"]) == {"TZ-101", "TZ-103"}


def test_unknown_stock_excluded(inventory):

    result = get_low_stock(inventory)

    assert "TZ-104" not in result["product_id"].values


def test_search_by_category(inventory):

    result = search_products(
        inventory,
        category="Saree"
    )

    assert len(result) == 3


def test_search_by_price_range(inventory):

    result = search_products(
        inventory,
        min_price=150,
        max_price=350
    )

    assert set(result["product_id"]) == {"TZ-102", "TZ-103"}


def test_inventory_summary(inventory):

    result = get_inventory_summary(inventory)

    assert result["total_inventory_records"] == 4
    assert result["unique_products"] == 4
    assert result["total_known_stock"] == 6
    assert result["missing_stock_records"] == 1
    assert result["inventory_value"] == 1100
    assert result["branch_count"] == 2


def test_reorder_suggestions(inventory):

    result = get_reorder_suggestions(inventory)

    assert set(result["product_id"]) == {"TZ-101", "TZ-103"}

    quantities = dict(zip(
        result["product_id"],
        result["suggested_reorder_qty"]
    ))

    assert quantities["TZ-101"] == 2
    assert quantities["TZ-103"] == 2


def test_branch_specific_low_stock(inventory):

    result = get_low_stock(inventory, "Branch 2")

    assert set(result["product_id"]) == {"TZ-103"}



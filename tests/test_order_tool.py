from app.order_tool import lookup_order


def test_missing_order_id():
    result = lookup_order(None)

    assert result["found"] is False
    assert result["error"] == "missing_order_id"


def test_invalid_order_id():
    result = lookup_order("hello")

    assert result["found"] is False
    assert result["error"] == "invalid_order_id"


def test_unknown_order_id():
    result = lookup_order("ORD-999999")

    assert result["found"] is False
    assert result["error"] == "order_not_found"


def test_order_id_normalization():
    result = lookup_order("  ord-1001  ")

    assert result["found"] is True
    assert result["order"]["order_id"] == "ORD-1001"


def test_customer_sensitive_fields_are_not_exposed():
    result = lookup_order("ORD-1001")

    assert result["found"] is True

    order = result["order"]

    assert "customer" not in order
    assert "email" not in order
    assert "shipping_address" not in order
    assert "internal" not in order
    assert "risk_score" not in order
    assert "warehouse_note" not in order
    assert "support_tags" not in order


def test_items_only_contain_safe_fields():
    result = lookup_order("ORD-1001")

    assert result["found"] is True

    items = result["order"]["items"]

    assert items

    for item in items:

        assert "name" in item
        assert "quantity" in item
        assert "final_sale" in item

        assert "sku" not in item


def test_lookup_returns_current_status():
    result = lookup_order("ORD-1001")

    assert result["found"] is True

    assert result["order"]["status"] == "pending"

def test_cancelled_order_does_not_show_stale_delivery_data():
    result = lookup_order("ORD-1004")

    assert result["found"] is True

    order = result["order"]

    assert order["status"] == "cancelled"

    assert "estimated_delivery" not in order
    assert "tracking_number" not in order
    assert "carrier" not in order
    assert "shipped_at" not in order


def test_returned_order_does_not_show_stale_delivery_data():
    result = lookup_order("ORD-1008")

    assert result["found"] is True

    order = result["order"]

    assert order["status"] == "returned"

    assert "estimated_delivery" not in order
    assert "tracking_number" not in order
    assert "carrier" not in order
    assert "shipped_at" not in order


def test_shipped_order_without_estimate_does_not_invent_date():
    result = lookup_order("ORD-1011")

    assert result["found"] is True

    order = result["order"]

    assert order["status"] == "shipped"
    assert order["estimated_delivery"] is None


def test_exception_order_is_identified():
    result = lookup_order("ORD-1010")

    assert result["found"] is True

    order = result["order"]

    assert order["status"] == "exception"


def test_processing_order_without_estimate_has_no_invented_date():
    result = lookup_order("ORD-1012")

    assert result["found"] is True

    order = result["order"]

    assert order["status"] == "processing"
    assert order["estimated_delivery"] is None
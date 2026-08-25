import json
import re
from pathlib import Path
from typing import Any


ORDERS_FILE = Path("data/orders.json")


# Fields that are safe to send to the customer/model.
CUSTOMER_SAFE_FIELDS = {
    "order_id",
    "membership_tier",
    "placed_at",
    "status",
    "status_updated_at",
    "shipped_at",
    "delivered_at",
    "carrier",
    "tracking_number",
    "estimated_delivery",
    "customer_safe_message",
}


# Safe fields inside each order item.
SAFE_ITEM_FIELDS = {
    "name",
    "quantity",
    "final_sale",
}


def normalize_order_id(order_id: str) -> str:
    """
    Normalize harmless differences in an order ID.

    Examples:
        " ord-1007 " -> "ORD-1007"
        "ORD-1007."  -> "ORD-1007"
        "ord-1007"   -> "ORD-1007"
    """

    if not isinstance(order_id, str):
        return ""

    normalized = order_id.strip().upper()

    # Remove harmless punctuation around the ID.
    normalized = normalized.strip(".,!?")

    return normalized


def load_orders() -> dict[str, dict[str, Any]]:
    """
    Load orders from the mock dataset.

    The complete dataset stays inside the application.
    It is never returned directly to the model.
    """

    with ORDERS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    return {
        order["order_id"]: order
        for order in data["orders"]
    }


# Load the orders once when this module is imported.
ORDERS_BY_ID = load_orders()


def sanitize_order(
    order: dict[str, Any],
) -> dict[str, Any]:
    """
    Return only customer-safe order information.

    Never expose:
        - customer name
        - customer email
        - shipping address
        - internal notes
        - risk scores
        - warehouse notes
        - support tags
    """

    result = {}

    # --------------------------------------------------
    # Safe top-level fields
    # --------------------------------------------------

    for field in CUSTOMER_SAFE_FIELDS:

        if field in order:
            result[field] = order[field]

    # --------------------------------------------------
    # Safe item fields
    # --------------------------------------------------

    if "items" in order:

        result["items"] = []

        for item in order["items"]:

            safe_item = {}

            for field in SAFE_ITEM_FIELDS:

                if field in item:
                    safe_item[field] = item[field]

            result["items"].append(
                safe_item
            )

    return result


def apply_status_rules(
    order: dict[str, Any],
    safe_order: dict[str, Any],
) -> dict[str, Any]:
    """
    Apply business rules to delivery-related fields.

    Cancelled and returned orders may contain stale
    delivery information in the original dataset.

    We must not expose those fields as if the order
    is still being delivered.
    """

    status = order.get("status")

    # --------------------------------------------------
    # Cancelled / returned
    # --------------------------------------------------

    if status in {
        "cancelled",
        "returned",
    }:

        safe_order.pop(
            "estimated_delivery",
            None,
        )

        safe_order.pop(
            "carrier",
            None,
        )

        safe_order.pop(
            "tracking_number",
            None,
        )

        safe_order.pop(
            "shipped_at",
            None,
        )

    return safe_order


def lookup_order(
    order_id: str,
) -> dict:
    """
    Safely look up a single order.

    The model receives only sanitized customer-safe data.
    """

    # Missing input
    if order_id is None:

        return {
            "found": False,
            "error": "missing_order_id",
            "message": (
                "Please provide your order ID."
            ),
        }

    # Normalize
    normalized = normalize_order_id(
        order_id
    )

    # Empty / invalid input
    if not normalized:

        return {
            "found": False,
            "error": "invalid_order_id",
            "message": (
                "Please provide a valid order ID."
            ),
        }

    # Require the expected ORD- format.
    if not re.fullmatch(
        r"ORD-[A-Z0-9]+",
        normalized,
    ):

        return {
            "found": False,
            "error": "invalid_order_id",
            "message": (
                f"{normalized} is not a valid order ID."
            ),
        }

    # Exact lookup.
    order = ORDERS_BY_ID.get(
        normalized
    )

    # Never guess a different order.
    if order is None:

        return {
            "found": False,
            "error": "order_not_found",
            "message": (
                f"I could not find an order matching "
                f"{normalized}."
            ),
        }

    # Sanitize before returning anything.
    safe_order = sanitize_order(
        order
    )

    # Apply cancelled / returned rules.
    safe_order = apply_status_rules(
        order,
        safe_order,
    )

    return {
        "found": True,
        "error": None,
        "order": safe_order,
    }
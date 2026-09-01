import json
from pathlib import Path


ORDERS_FILE = Path("data/orders.json")


with ORDERS_FILE.open(
    "r",
    encoding="utf-8",
) as file:
    data = json.load(file)


for order in data["orders"]:
    print(
        order["order_id"],
        "|",
        order["status"],
        "| estimate:",
        order.get("estimated_delivery"),
    )
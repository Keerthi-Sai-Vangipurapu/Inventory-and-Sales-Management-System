"""Reporting and bill history functions."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime

from utils import (
    RESTOCK_TARGET_DAYS,
    format_currency,
    load_inventory_data,
    load_transactions_data,
    parse_iso_datetime,
    pause,
    print_table,
    print_title,
)


def _product_name(inventory_data: dict, product_id: str, fallback_name: str = "") -> str:
    """Return a safe product display name."""
    product = inventory_data["products"].get(product_id)
    if product:
        return product["name"]
    if fallback_name:
        return fallback_name
    return f"Removed Product ({product_id})"


def _sales_by_product(transactions: list[dict]) -> dict[str, dict]:
    """Aggregate quantity and profit by product."""
    totals: dict[str, dict] = defaultdict(lambda: {"quantity": 0, "profit": 0.0, "name": ""})

    for transaction in transactions:
        for item in transaction["items"]:
            totals[item["product_id"]]["quantity"] += item["quantity"]
            totals[item["product_id"]]["profit"] += item["profit"]
            totals[item["product_id"]]["name"] = item["name"]

    return totals


def show_sales_report() -> None:
    """Display daily sales and best-selling product information."""
    print_title("Sales Report")
    inventory_data = load_inventory_data()
    transactions_data = load_transactions_data()
    today = datetime.now().date()

    todays_transactions = [
        transaction
        for transaction in transactions_data["transactions"]
        if parse_iso_datetime(transaction["timestamp"]).date() == today
    ]
    total_sales_today = sum(item["quantity"] for transaction in todays_transactions for item in transaction["items"])
    total_revenue_today = sum(transaction["total_amount"] for transaction in todays_transactions)

    totals = _sales_by_product(transactions_data["transactions"])
    sold_products = {product_id: details for product_id, details in totals.items() if details["quantity"] > 0}

    print(f"Total Sales Today : {total_sales_today} units")
    print(f"Total Revenue     : {format_currency(total_revenue_today)}")

    if sold_products:
        most_sold_id = max(sold_products, key=lambda product_id: sold_products[product_id]["quantity"])
        least_sold_id = min(sold_products, key=lambda product_id: sold_products[product_id]["quantity"])
        print(
            f"Most Sold Product : {_product_name(inventory_data, most_sold_id, sold_products[most_sold_id]['name'])} "
            f"({sold_products[most_sold_id]['quantity']} sold)"
        )
        print(
            f"Least Sold Product: {_product_name(inventory_data, least_sold_id, sold_products[least_sold_id]['name'])} "
            f"({sold_products[least_sold_id]['quantity']} sold)"
        )
    else:
        print("Most Sold Product : N/A")
        print("Least Sold Product: N/A")

    pause()


def show_profit_report() -> None:
    """Display overall profit and profit per product."""
    print_title("Profit Report")
    transactions_data = load_transactions_data()
    totals = _sales_by_product(transactions_data["transactions"])
    total_profit = sum(transaction["total_profit"] for transaction in transactions_data["transactions"])

    rows = [
        [details["name"], format_currency(details["profit"])]
        for _, details in sorted(totals.items(), key=lambda record: record[1]["name"])
    ]

    print_table(["Product", "Profit"], rows)
    print(f"\nTotal Profit = {format_currency(total_profit)}")
    pause()


def show_transaction_history() -> None:
    """Display previous bills and allow the user to inspect one."""
    print_title("Transaction History")
    transactions_data = load_transactions_data()
    transactions = transactions_data["transactions"]

    rows = [
        [
            transaction["bill_number"],
            parse_iso_datetime(transaction["timestamp"]).strftime("%Y-%m-%d %I:%M %p"),
            str(sum(item["quantity"] for item in transaction["items"])),
            format_currency(transaction["total_amount"]),
        ]
        for transaction in transactions
    ]
    print_table(["Bill No", "Date", "Items", "Total Amount"], rows)

    if not transactions:
        pause()
        return

    bill_number = input("\nEnter Bill Number to view details or press Enter to go back: ").strip()
    if not bill_number:
        pause()
        return

    transaction = next(
        (record for record in transactions if str(record["bill_number"]) == bill_number),
        None,
    )
    if not transaction:
        print("\nBill not found.")
        pause()
        return

    print()
    print_title(f"Bill No: {transaction['bill_number']}")
    print(f"Date: {transaction['timestamp']}\n")
    detail_rows = [
        [
            item["product_id"],
            item["name"],
            str(item["quantity"]),
            format_currency(item["unit_price"]),
            format_currency(item["line_total"]),
        ]
        for item in transaction["items"]
    ]
    print_table(["ID", "Product", "Qty", "Price", "Line Total"], detail_rows)
    print(f"\nTotal Amount: {format_currency(transaction['total_amount'])}")
    print(f"Total Profit: {format_currency(transaction['total_profit'])}")
    pause()


def show_restock_predictions() -> None:
    """Display predicted stock runout and recommended restock levels."""
    print_title("Restock Prediction")
    inventory_data = load_inventory_data()
    transactions_data = load_transactions_data()
    today = datetime.now().date()
    rows = []

    for product_id, product in sorted(inventory_data["products"].items()):
        daily_totals: dict[str, int] = defaultdict(int)
        for transaction in transactions_data["transactions"]:
            transaction_date = parse_iso_datetime(transaction["timestamp"]).date().isoformat()
            for item in transaction["items"]:
                if item["product_id"] == product_id:
                    daily_totals[transaction_date] += item["quantity"]

        total_sold = sum(daily_totals.values())
        if daily_totals:
            first_sale_date = min(datetime.fromisoformat(day).date() for day in daily_totals)
            observed_days = max((today - first_sale_date).days + 1, 1)
            avg_sales = total_sold / observed_days
            days_left = product["stock_quantity"] / avg_sales if avg_sales else math.inf
            recommended_restock = max(
                math.ceil(avg_sales * RESTOCK_TARGET_DAYS - product["stock_quantity"]),
                0,
            )
            days_left_text = f"{days_left:.1f} days" if math.isfinite(days_left) else "N/A"
        else:
            avg_sales = 0.0
            days_left_text = "N/A"
            recommended_restock = 0

        rows.append(
            [
                product_id,
                product["name"],
                str(product["stock_quantity"]),
                f"{avg_sales:.2f}",
                days_left_text,
                str(recommended_restock),
            ]
        )

    print_table(
        ["ID", "Product", "Stock", "Avg Sales", "Runs Out In", "Recommended Restock"],
        rows,
    )

    print("\nPrediction Notes:")
    for row in rows:
        product_name = row[1]
        if row[3] == "0.00":
            print(f"{product_name}: Not enough sales data for prediction.")
        else:
            print(
                f"{product_name} will run out in {row[4].replace(' days', '')} days | "
                f"Recommended Restock: {row[5]} units"
            )

    pause()

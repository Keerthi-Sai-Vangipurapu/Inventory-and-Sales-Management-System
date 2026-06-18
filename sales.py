"""Sales cart and billing logic."""

from __future__ import annotations

from qr import scan_qr_webcam
from utils import (
    format_currency,
    generate_bill_number,
    load_inventory_data,
    load_transactions_data,
    pause,
    print_message,
    print_separator,
    print_table,
    print_title,
    prompt_int,
    prompt_non_empty,
    prompt_yes_no,
    save_inventory_data,
    save_transactions_data,
    timestamp_now,
)


CURRENT_CART: list[dict] = []


def _get_product(data: dict, product_id: str) -> dict | None:
    """Fetch a product from inventory."""
    return data["products"].get(product_id)


def _reserved_quantity(product_id: str) -> int:
    """Return quantity already reserved in the current cart."""
    for item in CURRENT_CART:
        if item["product_id"] == product_id:
            return item["quantity"]
    return 0


def _cart_item(product_id: str) -> dict | None:
    """Return an existing cart item when present."""
    for item in CURRENT_CART:
        if item["product_id"] == product_id:
            return item
    return None


def _build_cart_item(product_id: str, product: dict, quantity: int) -> dict:
    """Create a cart line item."""
    return {
        "product_id": product_id,
        "name": product["name"],
        "quantity": quantity,
        "unit_price": round(product["selling_price"], 2),
        "cost_price": round(product["cost_price"], 2),
        "line_total": round(product["selling_price"] * quantity, 2),
        "profit": round((product["selling_price"] - product["cost_price"]) * quantity, 2),
    }


def _add_product_to_cart(product_id: str) -> None:
    """Add a product to the current bill cart."""
    data = load_inventory_data()
    product = _get_product(data, product_id)

    if not product:
        print_message("Product not found.")
        pause()
        return

    print(f"\nProduct: {product['name']}")
    print(f"Available Stock: {product['stock_quantity']}")
    quantity = prompt_int("Enter Quantity: ")

    reserved = _reserved_quantity(product_id)
    available_to_add = product["stock_quantity"] - reserved
    if quantity > available_to_add:
        print_message(f"Only {available_to_add} units available for this bill.")
        pause()
        return

    existing_item = _cart_item(product_id)
    new_quantity = quantity + reserved
    updated_item = _build_cart_item(product_id, product, new_quantity)

    if existing_item:
        existing_item.update(updated_item)
    else:
        CURRENT_CART.append(updated_item)

    print_message(
        f"Added to cart: {product['name']} x {quantity}\nCurrent Cart Total: {format_currency(cart_total())}"
    )
    pause()


def sell_using_product_id_interactive() -> None:
    """Add a cart item using a product id."""
    print_title("Sell Product Using Product ID")
    product_id = prompt_non_empty("Enter Product ID: ")
    _add_product_to_cart(product_id)


def sell_using_qr_interactive() -> None:
    """Add a cart item by scanning a QR code from the webcam."""
    print_title("Sell Product Using QR")
    print("Opening webcam scanner...")
    print("Hold the product QR code in front of the camera.")

    try:
        product_id = scan_qr_webcam()
    except (RuntimeError, ValueError) as error:
        print_message(str(error))
        pause()
        return

    print(f"\nScanned Product ID: {product_id}")
    _add_product_to_cart(product_id)


def cart_total() -> float:
    """Return the current cart total."""
    return round(sum(item["line_total"] for item in CURRENT_CART), 2)


def cart_item_count() -> int:
    """Return the number of distinct cart lines."""
    return len(CURRENT_CART)


def _print_cart() -> None:
    """Display the current cart."""
    rows = [
        [
            item["product_id"],
            item["name"],
            str(item["quantity"]),
            format_currency(item["unit_price"]),
            format_currency(item["line_total"]),
        ]
        for item in CURRENT_CART
    ]
    print_table(["ID", "Product", "Qty", "Price", "Line Total"], rows)
    print_separator()
    print(f"Cart Total: {format_currency(cart_total())}")


def _print_bill(transaction: dict) -> None:
    """Display a formatted bill."""
    print_title(f"Bill No: {transaction['bill_number']}")
    print(f"Date: {transaction['timestamp']}\n")

    rows = [
        [
            item["name"],
            str(item["quantity"]),
            format_currency(item["unit_price"]),
            format_currency(item["line_total"]),
        ]
        for item in transaction["items"]
    ]
    print_table(["Product", "Qty", "Price", "Line Total"], rows)
    print_separator()
    print(f"Total : {format_currency(transaction['total_amount'])}")
    print(f"Profit: {format_currency(transaction['total_profit'])}")


def generate_bill_interactive() -> None:
    """Create a bill from the current cart and save the transaction."""
    print_title("Generate Bill")
    if not CURRENT_CART:
        print_message("Cart is empty. Add products before generating a bill.")
        pause()
        return

    _print_cart()
    if not prompt_yes_no("\nGenerate bill now? (y/n): "):
        print_message("Bill generation cancelled.")
        pause()
        return

    inventory_data = load_inventory_data()
    for item in CURRENT_CART:
        product = _get_product(inventory_data, item["product_id"])
        if not product:
            print_message(f"Product {item['product_id']} no longer exists.")
            pause()
            return
        if item["quantity"] > product["stock_quantity"]:
            print_message(f"Insufficient stock for {product['name']}. Please rebuild the cart.")
            pause()
            return

    transactions_data = load_transactions_data()
    bill_number = generate_bill_number(transactions_data)
    timestamp = timestamp_now()
    transaction_items = [dict(item) for item in CURRENT_CART]

    for item in transaction_items:
        inventory_data["products"][item["product_id"]]["stock_quantity"] -= item["quantity"]
        inventory_data["products"][item["product_id"]]["updated_at"] = timestamp

    transaction = {
        "bill_number": bill_number,
        "timestamp": timestamp,
        "items": transaction_items,
        "total_amount": round(sum(item["line_total"] for item in transaction_items), 2),
        "total_profit": round(sum(item["profit"] for item in transaction_items), 2),
    }

    transactions_data["transactions"].append(transaction)
    transactions_data["last_bill_number"] = int(bill_number)

    save_inventory_data(inventory_data)
    save_transactions_data(transactions_data)

    CURRENT_CART.clear()
    _print_bill(transaction)
    pause()

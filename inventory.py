"""Inventory management logic."""

from __future__ import annotations

import os

from qr import generate_qr_code, scan_qr_webcam
from utils import (
    LOW_STOCK_THRESHOLD,
    format_currency,
    generate_product_id,
    load_inventory_data,
    pause,
    print_message,
    print_table,
    print_title,
    prompt_float,
    prompt_int,
    prompt_non_empty,
    prompt_optional_float,
    prompt_optional_int,
    prompt_optional_text,
    prompt_yes_no,
    resolve_project_path,
    save_inventory_data,
    timestamp_now,
)


def get_product_by_id(data: dict, product_id: str) -> dict | None:
    """Return a product from the inventory."""
    return data["products"].get(product_id)


def get_product_by_qr(data: dict) -> tuple[str, dict]:
    """Scan a QR code from the webcam and return the matched product."""
    product_id = scan_qr_webcam()
    product = get_product_by_id(data, product_id)
    if not product:
        raise ValueError(f"No product found for Product ID {product_id}.")
    return product_id, product


def add_product_interactive() -> None:
    """Add a new product and generate its QR code."""
    print_title("Add Product")
    data = load_inventory_data()

    name = prompt_non_empty("Enter Product Name: ")
    category = prompt_non_empty("Enter Category: ")
    cost_price = prompt_float("Enter Cost Price: ")
    selling_price = prompt_float("Enter Selling Price: ")
    stock_quantity = prompt_int("Enter Stock Quantity: ", allow_zero=True)

    product_id = generate_product_id(data)
    timestamp = timestamp_now()

    try:
        qr_code_path = generate_qr_code(product_id)
    except RuntimeError as error:
        print_message(str(error))
        pause()
        return

    data["products"][product_id] = {
        "product_id": product_id,
        "name": name,
        "category": category,
        "cost_price": cost_price,
        "selling_price": selling_price,
        "stock_quantity": stock_quantity,
        "qr_code_path": qr_code_path,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    data["last_product_number"] = int(product_id)
    save_inventory_data(data)

    print_message(
        f"Product added successfully.\nProduct ID: {product_id}\nQR Code: {qr_code_path}"
    )
    pause()


def update_product_by_id_interactive() -> None:
    """Update product details using a product id."""
    print_title("Update Product Using Product ID")
    data = load_inventory_data()
    product_id = prompt_non_empty("Enter Product ID: ")
    product = get_product_by_id(data, product_id)

    if not product:
        print_message("Product not found.")
        pause()
        return

    print("\nPress Enter to keep the current value.\n")
    print(f"Current Category      : {product['category']}")
    category = prompt_optional_text("New Category: ", product["category"])

    print(f"Current Cost Price    : {format_currency(product['cost_price'])}")
    cost_price = prompt_optional_float("New Cost Price: ", product["cost_price"])

    print(f"Current Selling Price : {format_currency(product['selling_price'])}")
    selling_price = prompt_optional_float("New Selling Price: ", product["selling_price"])

    print(f"Current Stock         : {product['stock_quantity']}")
    stock_quantity = prompt_optional_int("New Stock Quantity: ", product["stock_quantity"])

    product.update(
        {
            "category": category,
            "cost_price": cost_price,
            "selling_price": selling_price,
            "stock_quantity": stock_quantity,
            "updated_at": timestamp_now(),
        }
    )
    save_inventory_data(data)
    print_message("Product updated successfully.")
    pause()


def update_product_by_qr_interactive() -> None:
    """Scan a QR code from the webcam and update the matched product stock."""
    print_title("Update Product Using QR")
    data = load_inventory_data()
    print("Opening webcam scanner...")
    print("Hold the product QR code in front of the camera.")

    try:
        product_id, product = get_product_by_qr(data)
    except (RuntimeError, ValueError) as error:
        print_message(str(error))
        pause()
        return

    print(f"\nProduct ID   : {product_id}")
    print(f"Product Name : {product['name']}")
    print(f"Current Stock: {product['stock_quantity']}")
    stock_quantity = prompt_int("Enter New Stock Quantity: ", allow_zero=True)

    product["stock_quantity"] = stock_quantity
    product["updated_at"] = timestamp_now()
    save_inventory_data(data)
    print_message("Stock updated successfully using QR.")
    pause()


def delete_product_interactive() -> None:
    """Delete a product by id and remove its QR file when available."""
    print_title("Delete Product")
    data = load_inventory_data()
    product_id = prompt_non_empty("Enter Product ID to delete: ")
    product = get_product_by_id(data, product_id)

    if not product:
        print_message("Product not found.")
        pause()
        return

    print(f"\nProduct: {product['name']} | Stock: {product['stock_quantity']}")
    if not prompt_yes_no("Delete this product? (y/n): "):
        print_message("Delete cancelled.")
        pause()
        return

    qr_path = resolve_project_path(product["qr_code_path"])
    if os.path.exists(qr_path):
        os.remove(qr_path)

    del data["products"][product_id]
    save_inventory_data(data)
    print_message("Product deleted successfully.")
    pause()


def view_inventory() -> None:
    """Display all products in a table."""
    print_title("Inventory")
    data = load_inventory_data()

    rows = []
    for product_id, product in sorted(data["products"].items()):
        status = "Low Stock" if product["stock_quantity"] <= LOW_STOCK_THRESHOLD else "OK"
        rows.append(
            [
                product_id,
                product["name"],
                product["category"],
                format_currency(product["cost_price"]),
                format_currency(product["selling_price"]),
                str(product["stock_quantity"]),
                product["qr_code_path"],
                status,
            ]
        )

    print_table(
        ["ID", "Name", "Category", "Cost", "Sell", "Stock", "QR Path", "Status"],
        rows,
    )
    pause()

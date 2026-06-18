"""Shared helpers for the inventory system."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any, Callable


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
TRANSACTIONS_FILE = os.path.join(BASE_DIR, "transactions.json")
QR_CODES_DIR = os.path.join(BASE_DIR, "qr_codes")
LOW_STOCK_THRESHOLD = 5
RESTOCK_TARGET_DAYS = 7


def _sample_timestamp(days_ago: int, hour: int, minute: int) -> str:
    """Create sample timestamps relative to the current local time."""
    stamp = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    stamp -= timedelta(days=days_ago)
    return stamp.isoformat(timespec="seconds")


def relative_qr_path(product_id: str) -> str:
    """Return the stored relative QR image path for a product."""
    return os.path.join("qr_codes", f"{product_id}.png")


def get_default_inventory_data() -> dict[str, Any]:
    """Return default inventory data used on first run."""
    return {
        "last_product_number": 104,
        "products": {
            "101": {
                "product_id": "101",
                "name": "Milk",
                "category": "Dairy",
                "cost_price": 20.0,
                "selling_price": 25.0,
                "stock_quantity": 18,
                "qr_code_path": relative_qr_path("101"),
                "created_at": _sample_timestamp(4, 9, 0),
                "updated_at": _sample_timestamp(0, 10, 15),
            },
            "102": {
                "product_id": "102",
                "name": "Bread",
                "category": "Bakery",
                "cost_price": 30.0,
                "selling_price": 40.0,
                "stock_quantity": 4,
                "qr_code_path": relative_qr_path("102"),
                "created_at": _sample_timestamp(4, 9, 5),
                "updated_at": _sample_timestamp(0, 11, 10),
            },
            "103": {
                "product_id": "103",
                "name": "Rice",
                "category": "Groceries",
                "cost_price": 45.0,
                "selling_price": 60.0,
                "stock_quantity": 28,
                "qr_code_path": relative_qr_path("103"),
                "created_at": _sample_timestamp(4, 9, 10),
                "updated_at": _sample_timestamp(1, 16, 40),
            },
            "104": {
                "product_id": "104",
                "name": "Eggs",
                "category": "Dairy",
                "cost_price": 4.0,
                "selling_price": 6.0,
                "stock_quantity": 60,
                "qr_code_path": relative_qr_path("104"),
                "created_at": _sample_timestamp(4, 9, 15),
                "updated_at": _sample_timestamp(0, 12, 25),
            },
        },
    }


def get_default_transactions_data() -> dict[str, Any]:
    """Return starter bill history."""
    return {
        "last_bill_number": 102,
        "transactions": [
            {
                "bill_number": "101",
                "timestamp": _sample_timestamp(1, 10, 15),
                "items": [
                    {
                        "product_id": "101",
                        "name": "Milk",
                        "quantity": 2,
                        "unit_price": 25.0,
                        "cost_price": 20.0,
                        "line_total": 50.0,
                        "profit": 10.0,
                    },
                    {
                        "product_id": "102",
                        "name": "Bread",
                        "quantity": 1,
                        "unit_price": 40.0,
                        "cost_price": 30.0,
                        "line_total": 40.0,
                        "profit": 10.0,
                    },
                ],
                "total_amount": 90.0,
                "total_profit": 20.0,
            },
            {
                "bill_number": "102",
                "timestamp": _sample_timestamp(0, 11, 30),
                "items": [
                    {
                        "product_id": "104",
                        "name": "Eggs",
                        "quantity": 12,
                        "unit_price": 6.0,
                        "cost_price": 4.0,
                        "line_total": 72.0,
                        "profit": 24.0,
                    },
                    {
                        "product_id": "103",
                        "name": "Rice",
                        "quantity": 3,
                        "unit_price": 60.0,
                        "cost_price": 45.0,
                        "line_total": 180.0,
                        "profit": 45.0,
                    },
                ],
                "total_amount": 252.0,
                "total_profit": 69.0,
            },
        ],
    }


def _is_valid_inventory_data(data: dict[str, Any]) -> bool:
    return isinstance(data, dict) and "last_product_number" in data and "products" in data


def _is_valid_transactions_data(data: dict[str, Any]) -> bool:
    return isinstance(data, dict) and "last_bill_number" in data and "transactions" in data


def _load_json_file(
    path: str,
    default_factory: Callable[[], dict[str, Any]],
    validator: Callable[[dict[str, Any]], bool],
) -> dict[str, Any]:
    """Load JSON data and recreate the file if it is missing or invalid."""
    if not os.path.exists(path):
        data = default_factory()
        _save_json_file(path, data)
        return data

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        data = default_factory()
        _save_json_file(path, data)
        return data

    if not validator(data):
        data = default_factory()
        _save_json_file(path, data)
        return data

    return data


def _save_json_file(path: str, data: dict[str, Any]) -> None:
    """Write JSON data to disk."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def ensure_app_files() -> None:
    """Create missing folders and seed data files on first run."""
    os.makedirs(QR_CODES_DIR, exist_ok=True)
    load_inventory_data()
    load_transactions_data()


def load_inventory_data() -> dict[str, Any]:
    """Load the inventory database."""
    return _load_json_file(DATA_FILE, get_default_inventory_data, _is_valid_inventory_data)


def save_inventory_data(data: dict[str, Any]) -> None:
    """Persist the inventory database."""
    _save_json_file(DATA_FILE, data)


def load_transactions_data() -> dict[str, Any]:
    """Load saved bill transactions."""
    return _load_json_file(
        TRANSACTIONS_FILE,
        get_default_transactions_data,
        _is_valid_transactions_data,
    )


def save_transactions_data(data: dict[str, Any]) -> None:
    """Persist bill transactions."""
    _save_json_file(TRANSACTIONS_FILE, data)


def generate_product_id(data: dict[str, Any]) -> str:
    """Return the next product id without mutating the caller."""
    return str(int(data.get("last_product_number", 100)) + 1)


def generate_bill_number(transactions_data: dict[str, Any]) -> str:
    """Return the next bill number without mutating the caller."""
    return str(int(transactions_data.get("last_bill_number", 100)) + 1)


def resolve_project_path(path_value: str) -> str:
    """Resolve a stored relative path to an absolute path."""
    if os.path.isabs(path_value):
        return path_value
    return os.path.join(BASE_DIR, path_value)


def timestamp_now() -> str:
    """Return the current local timestamp."""
    return datetime.now().isoformat(timespec="seconds")


def parse_iso_datetime(value: str) -> datetime:
    """Parse an ISO timestamp."""
    return datetime.fromisoformat(value)


def format_currency(value: float) -> str:
    """Format currency for terminal display."""
    return f"{value:.2f}"


def print_separator(char: str = "-", length: int = 78) -> None:
    """Print a separator line."""
    print(char * length)


def print_title(title: str) -> None:
    """Print a simple title block."""
    print_separator("=")
    print(title)
    print_separator("=")


def print_message(message: str) -> None:
    """Print a message with consistent spacing."""
    print(f"\n{message}\n")


def print_table(headers: list[str], rows: list[list[Any]]) -> None:
    """Render a basic ASCII table."""
    prepared_rows = [[str(value) for value in row] for row in rows]
    widths = [len(str(header)) for header in headers]

    for row in prepared_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    header_line = " | ".join(str(header).ljust(widths[index]) for index, header in enumerate(headers))
    separator_line = "-+-".join("-" * width for width in widths)

    print(header_line)
    print(separator_line)

    if not prepared_rows:
        print("No records found.")
        return

    for row in prepared_rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def prompt_non_empty(message: str) -> str:
    """Prompt until a non-empty value is entered."""
    while True:
        value = input(message).strip()
        if value:
            return value
        print("Input cannot be empty. Please try again.")


def prompt_float(message: str, allow_zero: bool = False) -> float:
    """Prompt until a valid float is entered."""
    while True:
        value = input(message).strip()
        try:
            number = float(value)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if number < 0 or (number == 0 and not allow_zero):
            print("Please enter a number greater than zero.")
            continue
        return round(number, 2)


def prompt_int(message: str, allow_zero: bool = False) -> int:
    """Prompt until a valid integer is entered."""
    while True:
        value = input(message).strip()
        if not value.isdigit():
            print("Please enter a valid whole number.")
            continue

        number = int(value)
        if number == 0 and not allow_zero:
            print("Please enter a number greater than zero.")
            continue
        return number


def prompt_optional_text(message: str, current_value: str) -> str:
    """Allow the user to keep an existing text value."""
    value = input(message).strip()
    return value or current_value


def prompt_optional_float(message: str, current_value: float) -> float:
    """Allow the user to keep an existing float value."""
    while True:
        value = input(message).strip()
        if not value:
            return current_value
        try:
            number = float(value)
        except ValueError:
            print("Please enter a valid number.")
            continue
        if number < 0:
            print("Please enter zero or a positive number.")
            continue
        return round(number, 2)


def prompt_optional_int(message: str, current_value: int) -> int:
    """Allow the user to keep an existing integer value."""
    while True:
        value = input(message).strip()
        if not value:
            return current_value
        if not value.isdigit():
            print("Please enter a valid whole number.")
            continue
        return int(value)


def prompt_yes_no(message: str) -> bool:
    """Prompt for a yes or no answer."""
    while True:
        value = input(message).strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please enter y or n.")


def pause() -> None:
    """Pause so the user can read the output."""
    input("\nPress Enter to continue...")

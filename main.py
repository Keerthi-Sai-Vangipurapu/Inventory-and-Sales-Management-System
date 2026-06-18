"""Main menu and application entry point."""

from __future__ import annotations

from inventory import (
    add_product_interactive,
    delete_product_interactive,
    update_product_by_id_interactive,
    update_product_by_qr_interactive,
    view_inventory,
)
from reports import show_profit_report, show_restock_predictions, show_sales_report, show_transaction_history
from sales import cart_item_count, generate_bill_interactive, sell_using_product_id_interactive, sell_using_qr_interactive
from utils import ensure_app_files, print_title


def inventory_menu() -> None:
    """Run the inventory submenu."""
    while True:
        print_title("Inventory Menu")
        print("1. Add Product (Generate QR automatically)")
        print("2. Update Product")
        print("3. Delete Product")
        print("4. View Inventory")
        print("5. Back to Main Menu")

        choice = input("\nEnter your choice: ").strip()
        print()

        if choice == "1":
            add_product_interactive()
        elif choice == "2":
            update_product_menu()
        elif choice == "3":
            delete_product_interactive()
        elif choice == "4":
            view_inventory()
        elif choice == "5":
            return
        else:
            print("Invalid choice. Please try again.\n")


def update_product_menu() -> None:
    """Run the update product submenu."""
    while True:
        print_title("Update Product")
        print("1. Update using Product ID")
        print("2. Update using QR")
        print("3. Back")

        choice = input("\nEnter your choice: ").strip()
        print()

        if choice == "1":
            update_product_by_id_interactive()
        elif choice == "2":
            update_product_by_qr_interactive()
        elif choice == "3":
            return
        else:
            print("Invalid choice. Please try again.\n")


def sell_product_menu() -> None:
    """Run the sell product submenu."""
    while True:
        print_title("Sell Product")
        print("1. Sell using Product ID")
        print("2. Sell using QR")
        print("3. Back")

        choice = input("\nEnter your choice: ").strip()
        print()

        if choice == "1":
            sell_using_product_id_interactive()
        elif choice == "2":
            sell_using_qr_interactive()
        elif choice == "3":
            return
        else:
            print("Invalid choice. Please try again.\n")


def sales_menu() -> None:
    """Run the sales submenu."""
    while True:
        print_title("Sales Menu")
        print("1. Sell Product")
        print("2. Generate Bill")
        print("3. Sales Report")
        print("4. Profit Report")
        print("5. Transaction History")
        print("6. Back to Main Menu")

        if cart_item_count():
            print(f"\nPending cart lines: {cart_item_count()}")

        choice = input("\nEnter your choice: ").strip()
        print()

        if choice == "1":
            sell_product_menu()
        elif choice == "2":
            generate_bill_interactive()
        elif choice == "3":
            show_sales_report()
        elif choice == "4":
            show_profit_report()
        elif choice == "5":
            show_transaction_history()
        elif choice == "6":
            return
        else:
            print("Invalid choice. Please try again.\n")


def main() -> None:
    """Run the application until the user chooses Exit."""
    ensure_app_files()

    while True:
        print_title("Inventory and Sales Management System")
        print("1. Inventory")
        print("2. Sales")
        print("3. Restock Prediction")
        print("4. Exit")

        choice = input("\nEnter your choice: ").strip()
        print()

        if choice == "1":
            inventory_menu()
        elif choice == "2":
            sales_menu()
        elif choice == "3":
            show_restock_predictions()
        elif choice == "4":
            print("Thank you for using the system.\n")
            break
        else:
            print("Invalid choice. Please try again.\n")


if __name__ == "__main__":
    main()

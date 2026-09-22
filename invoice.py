from datetime import datetime
from pathlib import Path

from config import (
    SHOP_NAME,
    SHOP_ADDRESS,
    SHOP_PHONE,
    CURRENCY
)


# ==========================================================
# CREATE INVOICE
# ==========================================================

def create_invoice(
    sale_id,
    customer_name,
    customer_phone,
    items,
    subtotal,
    discount,
    grand_total
):

    Path("invoices").mkdir(
        exist_ok=True
    )

    filename = Path(
        "invoices"
    ) / f"invoice_{sale_id}.txt"

    file = open(
        filename,
        "w",
        encoding="utf-8"
    )

    file.write("=" * 60 + "\n")
    file.write(SHOP_NAME + "\n")
    file.write(SHOP_ADDRESS + "\n")
    file.write(
        "Phone: "
        + SHOP_PHONE
        + "\n"
    )

    file.write("=" * 60 + "\n")

    file.write(
        "Invoice No: MT-"
        + str(sale_id)
        + "\n"
    )

    file.write(
        "Date: "
        + datetime.now().strftime(
            "%d-%m-%Y %I:%M %p"
        )
        + "\n"
    )

    file.write(
        "Customer: "
        + customer_name
        + "\n"
    )

    file.write(
        "Phone: "
        + str(customer_phone or "-")
        + "\n"
    )

    file.write("-" * 60 + "\n")

    file.write(
        "Medicine    Batch    Qty    Rate    Amount\n"
    )

    file.write("-" * 60 + "\n")

    for item in items:

        file.write(
            item["medicine_name"]
            + "    "
            + item["batch_no"]
            + "    "
            + str(item["quantity"])
            + "    "
            + str(item["unit_price"])
            + "    "
            + str(item["line_total"])
            + "\n"
        )

    file.write("-" * 60 + "\n")

    file.write(
        "Subtotal: "
        + CURRENCY
        + str(subtotal)
        + "\n"
    )

    file.write(
        "Discount: "
        + CURRENCY
        + str(discount)
        + "\n"
    )

    file.write(
        "Grand Total: "
        + CURRENCY
        + str(grand_total)
        + "\n"
    )

    file.write("\n")
    file.write(
        "Thank you for visiting Medi-Track.\n"
    )

    file.write(
        "Keep this invoice for your records.\n"
    )

    file.write("=" * 60 + "\n")

    file.close()

    return str(filename)
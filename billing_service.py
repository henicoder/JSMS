from decimal import Decimal


def calculate_item(product, quantity):
    """
    Calculate the complete price for a product.

    Calculation order:
    1. Base price
    2. Product discount
    3. Making charges
    4. GST
    5. Final total
    """

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    quantity = int(quantity)

    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    # --------------------------------------------------------
    # Original product price
    # --------------------------------------------------------

    unit_price = Decimal(
        str(product.price or 0)
    )

    base = unit_price * Decimal(quantity)

    # --------------------------------------------------------
    # Discount
    # --------------------------------------------------------

    discount_percent = Decimal(
        str(
            getattr(
                product,
                "discount_percent",
                0
            ) or 0
        )
    )

    if discount_percent < 0:
        discount_percent = Decimal("0")

    if discount_percent > 100:
        discount_percent = Decimal("100")

    discount = (
        base
        * discount_percent
        / Decimal("100")
    )

    discounted_base = base - discount

    # --------------------------------------------------------
    # Fixed making charge
    # --------------------------------------------------------

    making = (
        Decimal(
            str(
                product.making_charge or 0
            )
        )
        * Decimal(quantity)
    )

    # --------------------------------------------------------
    # Percentage making charge
    # --------------------------------------------------------

    if product.making_charge_percent:

        making += (
            discounted_base
            * Decimal(
                str(
                    product.making_charge_percent
                )
            )
            / Decimal("100")
        )

    # --------------------------------------------------------
    # Taxable amount
    # --------------------------------------------------------

    taxable = (
        discounted_base
        + making
    )

    # --------------------------------------------------------
    # GST
    # --------------------------------------------------------

    gst_rate = Decimal(
        str(
            product.gst_rate or 0
        )
    )

    gst = (
        taxable
        * gst_rate
        / Decimal("100")
    )

    # --------------------------------------------------------
    # Final total
    # --------------------------------------------------------

    total = taxable + gst

    return {
        "base": base,
        "discount_percent": discount_percent,
        "discount": discount,
        "discounted_base": discounted_base,
        "making": making,
        "taxable": taxable,
        "gst_rate": gst_rate,
        "gst": gst,
        "total": total
    }
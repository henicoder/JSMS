import os
from decimal import Decimal


def get_silver_rate():
    return Decimal(
        str(os.getenv("SILVER_925_RATE", "0"))
    )


def calculate_custom_jewellery(
    weight,
    making_charge,
    customization_charge
):
    weight = Decimal(str(weight))
    making_charge = Decimal(str(making_charge or 0))
    customization_charge = Decimal(
        str(customization_charge or 0)
    )

    silver_rate = get_silver_rate()

    silver_value = weight * silver_rate

    taxable_amount = (
        silver_value
        + making_charge
        + customization_charge
    )

    gst = taxable_amount * Decimal("0.03")

    final_amount = taxable_amount + gst

    return {
        "silver_rate": silver_rate,
        "silver_value": silver_value,
        "making_charge": making_charge,
        "customization_charge": customization_charge,
        "gst": gst,
        "final_amount": final_amount
    }
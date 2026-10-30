import os
from datetime import datetime


def get_metal_prices():
    """
    Returns configurable silver reference prices.

    These values come from environment variables.
    They are NOT claimed to be live market prices.
    """

    silver_925 = float(os.getenv("SILVER_925_RATE", "0"))

    return {
        "silver_925": silver_925,
        "updated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "source": "Configured reference rates"
    }


def calculate_metal_value(metal_type, purity, weight):
    """
    Estimate the metal value using configured rates.
    """

    if not weight:
        return 0

    try:
        weight = float(weight)
    except (ValueError, TypeError):
        return 0

    metal = (metal_type or "").lower()
    purity_value = (purity or "").lower()

    prices = get_metal_prices()

    if "silver" in metal and "925" in purity_value:
        return weight * prices["silver_925"]

    return 0
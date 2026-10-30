from decimal import Decimal, InvalidOperation
from datetime import datetime


def recommend_products(
    products,
    occasion=None,
    jewellery_type=None,
    budget=None,
    metal=None,
    purity=None,
    style=None,
    limit=8
):
    """
    Intelligent jewellery recommendation engine.

    Products are scored using:
    - Jewellery type
    - Metal
    - Purity
    - Budget
    - Style
    - Occasion
    - Discount
    - Stock availability
    - Product freshness

    Returns products sorted by recommendation score.
    """

    recommendations = []

    # --------------------------------------------------
    # Convert budget safely
    # --------------------------------------------------

    try:
        budget = Decimal(str(budget)) if budget else None
    except (ValueError, TypeError, InvalidOperation):
        budget = None

    # --------------------------------------------------
    # Normalize user inputs
    # --------------------------------------------------

    occasion = occasion.lower().strip() if occasion else None
    jewellery_type = jewellery_type.lower().strip() if jewellery_type else None
    metal = metal.lower().strip() if metal else None
    purity = purity.lower().strip() if purity else None
    style = style.lower().strip() if style else None

    # --------------------------------------------------
    # Occasion keywords
    # --------------------------------------------------

    occasion_keywords = {
        "wedding": [
            "wedding",
            "bridal",
            "bride",
            "marriage"
        ],

        "party": [
            "party",
            "partywear",
            "celebration"
        ],

        "daily": [
            "daily",
            "everyday",
            "casual"
        ],

        "office": [
            "office",
            "professional",
            "formal"
        ],

        "gift": [
            "gift",
            "present"
        ],

        "festival": [
            "festival",
            "festive",
            "traditional"
        ]
    }

    # --------------------------------------------------
    # Process every product
    # --------------------------------------------------

    for product in products:

        # Ignore inactive products
        if product.status != "active":
            continue

        # Ignore products that are out of stock
        if (product.stock_quantity or 0) <= 0:
            continue

        score = 0
        reasons = []

        # --------------------------------------------------
        # Product text
        # --------------------------------------------------

        name = (product.name or "").lower()
        description = (product.description or "").lower()
        metal_type = (product.metal_type or "").lower()
        product_purity = (product.purity or "").lower()

        searchable_text = (
            f"{name} {description} "
            f"{metal_type} {product_purity}"
        )

        # --------------------------------------------------
        # 1. Jewellery Type — 25 points
        # --------------------------------------------------

        if jewellery_type:

            if jewellery_type in searchable_text:

                score += 25

                reasons.append(
                    "Matches your jewellery type"
                )

        # --------------------------------------------------
        # 2. Metal — 20 points
        # --------------------------------------------------

        if metal:

            if metal in metal_type or metal in searchable_text:

                score += 20

                reasons.append(
                    "Matches your preferred metal"
                )

        # --------------------------------------------------
        # 3. Purity — 15 points
        # --------------------------------------------------

        if purity:

            if purity in product_purity:

                score += 15

                reasons.append(
                    "Matches your preferred purity"
                )

        # --------------------------------------------------
        # 4. Budget — 20 + bonus points
        # --------------------------------------------------

        try:
            price = Decimal(str(product.price))
        except (ValueError, TypeError, InvalidOperation):
            price = Decimal("0")

        if budget and price > 0:

            if price <= budget:

                score += 20

                reasons.append(
                    "Within your budget"
                )

                # Extra points if product is close to budget
                if price >= budget * Decimal("0.75"):

                    score += 5

                    reasons.append(
                        "Good value for your budget"
                    )

            else:

                difference = price - budget

                # Slightly above budget
                if difference <= budget * Decimal("0.10"):

                    score += 5

                    reasons.append(
                        "Slightly above your budget"
                    )

        # --------------------------------------------------
        # 5. Style — 10 points
        # --------------------------------------------------

        if style:

            if style in searchable_text:

                score += 10

                reasons.append(
                    "Matches your preferred style"
                )

        # --------------------------------------------------
        # 6. Occasion — 10 points
        # --------------------------------------------------

        if occasion:

            keywords = occasion_keywords.get(
                occasion,
                [occasion]
            )

            if any(
                keyword in searchable_text
                for keyword in keywords
            ):

                score += 10

                reasons.append(
                    "Suitable for your occasion"
                )

        # --------------------------------------------------
        # 7. Discount Bonus — 5 points
        # --------------------------------------------------

        discount = getattr(
            product,
            "discount_percent",
            0
        ) or 0

        try:
            discount = Decimal(str(discount))
        except (ValueError, TypeError, InvalidOperation):
            discount = Decimal("0")

        if discount > 0:

            score += 5

            reasons.append(
                f"{discount}% discount available"
            )

        # --------------------------------------------------
        # 8. Stock Bonus — up to 5 points
        # --------------------------------------------------

        stock = product.stock_quantity or 0

        if stock >= 5:

            score += 5

            reasons.append(
                "Currently well stocked"
            )

        elif stock > 0:

            score += 2

            reasons.append(
                "Currently available"
            )

        # --------------------------------------------------
        # 9. New Product Bonus
        # --------------------------------------------------

        created_at = getattr(
            product,
            "created_at",
            None
        )

        if created_at:

            try:

                days_old = (
                    datetime.utcnow() - created_at
                ).days

                if days_old <= 30:

                    score += 5

                    reasons.append(
                        "New arrival"
                    )

            except (TypeError, ValueError):

                pass

        # --------------------------------------------------
        # Only include meaningful recommendations
        # --------------------------------------------------

        if score > 0:

            recommendations.append({
                "product": product,
                "score": score,
                "reasons": reasons
            })

    # --------------------------------------------------
    # Highest score first
    # --------------------------------------------------

    recommendations.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return recommendations[:limit]
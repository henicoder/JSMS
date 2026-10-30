from datetime import datetime, timedelta
from sqlalchemy import func

from ..extensions import db
from ..models import Product, InventoryTransaction


def get_inventory_predictions(days=30, lead_time_days=15):
    """
    Generate inventory predictions using historical OUT transactions.

    days:
        Number of historical days used to calculate sales velocity.

    lead_time_days:
        Expected number of days required to replenish stock.
    """

    start_date = datetime.utcnow() - timedelta(days=days)

    products = Product.query.filter_by(
        status="active"
    ).all()

    predictions = []

    for product in products:

        # -----------------------------------------
        # Total units sold during analysis period
        # -----------------------------------------

        total_sold = (
            db.session.query(
                func.coalesce(
                    func.sum(InventoryTransaction.quantity),
                    0
                )
            )
            .filter(
                InventoryTransaction.product_id == product.id,
                InventoryTransaction.transaction_type == "OUT",
                InventoryTransaction.created_at >= start_date
            )
            .scalar()
        )

        total_sold = int(total_sold or 0)

        # -----------------------------------------
        # Average daily sales
        # -----------------------------------------

        average_daily_sales = total_sold / days

        current_stock = int(product.stock_quantity or 0)

        # -----------------------------------------
        # Estimated stockout
        # -----------------------------------------

        if average_daily_sales > 0:

            stockout_days = current_stock / average_daily_sales

        else:

            stockout_days = None

        # -----------------------------------------
        # Reorder calculation
        # -----------------------------------------

        lead_time_demand = (
            average_daily_sales *
            lead_time_days
        )

        safety_stock = (
            average_daily_sales *
            7
        )

        reorder_point = (
            lead_time_demand +
            safety_stock
        )

        recommended_reorder = max(
            0,
            round(reorder_point - current_stock)
        )

        # -----------------------------------------
        # Risk classification
        # -----------------------------------------

        if current_stock <= 0:

            risk = "CRITICAL"

        elif stockout_days is not None and stockout_days <= 7:

            risk = "CRITICAL"

        elif stockout_days is not None and stockout_days <= 15:

            risk = "HIGH"

        elif (
            stockout_days is not None
            and stockout_days <= 30
        ):

            risk = "MEDIUM"

        elif current_stock <= (
            product.low_stock_threshold or 3
        ):

            risk = "HIGH"

        else:

            risk = "LOW"

        predictions.append({
            "product": product,
            "current_stock": current_stock,
            "total_sold": total_sold,
            "average_daily_sales": round(
                average_daily_sales,
                2
            ),
            "stockout_days": (
                round(stockout_days, 1)
                if stockout_days is not None
                else None
            ),
            "reorder_point": round(
                reorder_point
            ),
            "recommended_reorder": recommended_reorder,
            "risk": risk
        })

    # Critical → High → Medium → Low
    risk_order = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    predictions.sort(
        key=lambda x: (
            risk_order[x["risk"]],
            x["stockout_days"]
            if x["stockout_days"] is not None
            else 999999
        )
    )

    return predictions
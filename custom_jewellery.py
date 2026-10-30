from datetime import datetime

from ..extensions import db


class CustomJewellery(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customer.id"),
        nullable=False
    )

    jewellery_type = db.Column(
        db.String(50),
        nullable=False
    )

    design_style = db.Column(
        db.String(50),
        nullable=False
    )

    silver_purity = db.Column(
        db.String(20),
        nullable=False,
        default="925"
    )

    weight = db.Column(
        db.Numeric(10, 3),
        nullable=False
    )

    size = db.Column(
        db.String(50)
    )

    finish = db.Column(
        db.String(50)
    )

    engraving = db.Column(
        db.String(255)
    )

    silver_rate_at_purchase = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    silver_value = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    making_charge = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    customization_charge = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    gst = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    final_amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Link custom jewellery to the normal Order system
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("order.id"),
        nullable=True
    )

    # Relationship with Customer
    customer = db.relationship(
        "Customer",
        backref="custom_jewellery_orders"
    )

    # Relationship with Order
    order = db.relationship(
        "Order",
        backref=db.backref(
            "custom_jewellery",
            uselist=False
        )
    )
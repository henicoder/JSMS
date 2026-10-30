from datetime import datetime

from ..extensions import db


class Payment(db.Model):

    __tablename__ = "payment"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    payment_id = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("order.id"),
        nullable=False
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customer.id"),
        nullable=False
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    payment_method = db.Column(
        db.String(40),
        nullable=False
    )

    transaction_id = db.Column(
        db.String(100)
    )

    payment_status = db.Column(
        db.String(30),
        default="Pending"
    )

    payment_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Relationship with Order
    order = db.relationship(
        "Order",
        backref=db.backref(
            "payment",
            uselist=False
        )
    )

    # Relationship with Customer
    customer = db.relationship(
        "Customer",
        backref="payments"
    )
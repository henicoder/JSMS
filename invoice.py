from datetime import datetime

from ..extensions import db


class Invoice(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    invoice_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("order.id"),
        unique=True,
        nullable=False
    )

    invoice_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    order = db.relationship(
        "Order",
        backref=db.backref(
            "invoice",
            uselist=False
        )
    )
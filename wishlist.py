from datetime import datetime
from ..extensions import db


class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customer.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    customer = db.relationship("Customer", backref="wishlist_items")
    product = db.relationship("Product")

    __table_args__ = (
        db.UniqueConstraint(
            "customer_id",
            "product_id",
            name="unique_customer_product_wishlist"
        ),
    )
from datetime import datetime

from ..extensions import db


class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    order_number = db.Column(
        db.String(40),
        unique=True,
        nullable=False,
        index=True
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customer.id"),
        nullable=False
    )

    order_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    subtotal = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    making_charges = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    discount = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    gst = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    total_amount = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    payment_status = db.Column(
        db.String(30),
        default="Pending"
    )

    order_status = db.Column(
        db.String(30),
        default="Pending"
    )

    shipping_address = db.Column(
        db.String(500)
    )

    # Relationship with Customer
    customer = db.relationship(
        "Customer",
        backref="orders"
    )

    # Relationship with OrderItem
    items = db.relationship(
        "OrderItem",
        backref="order",
        cascade="all, delete-orphan"
    )


class OrderItem(db.Model):
    __tablename__ = "order_item"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("order.id"),
        nullable=False
    )

    # Nullable because a custom jewellery item
    # does not have to exist in the Product table.
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=True
    )

    product_name = db.Column(
        db.String(160),
        nullable=False
    )

    sku = db.Column(
        db.String(60),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    unit_price = db.Column(
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

    gst_rate = db.Column(
        db.Numeric(5, 2),
        default=3
    )

    gst_amount = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    # Relationship with Product
    product = db.relationship(
        "Product"
    )
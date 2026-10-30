from ..extensions import db

supplier_products = db.Table(
    "supplier_products",
    db.Column("supplier_id", db.Integer, db.ForeignKey("supplier.id"), primary_key=True),
    db.Column("product_id", db.Integer, db.ForeignKey("product.id"), primary_key=True)
)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(120), nullable=False)
    company_name = db.Column(db.String(120))
    email = db.Column(db.String(160))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    status = db.Column(db.String(20), default="active")
    products = db.relationship("Product", secondary=supplier_products, backref="suppliers")

SupplierProduct = supplier_products

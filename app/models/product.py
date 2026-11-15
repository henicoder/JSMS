from datetime import datetime
from ..extensions import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(60), unique=True, nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    metal_type = db.Column(db.String(50))
    purity = db.Column(db.String(30))
    weight = db.Column(db.Numeric(10, 3))
    making_charge = db.Column(db.Numeric(12, 2), default=0)
    making_charge_percent = db.Column(db.Numeric(5, 2), default=0)
    gst_rate = db.Column(db.Numeric(5, 2), default=3)
    stock_quantity = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=3)
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="active")
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

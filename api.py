from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func
from ..extensions import db
from ..models import Product, Category, Order, Customer, Payment

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.get("/products")
def product_list():
    products = Product.query.filter_by(status="active").all()
    return jsonify([{
        "id": p.id, "sku": p.sku, "name": p.name, "price": float(p.price),
        "stock": p.stock_quantity, "category": p.category.name if p.category else None
    } for p in products])

@api_bp.get("/products/<int:product_id>")
def product_get(product_id):
    p = Product.query.get_or_404(product_id)
    return jsonify({"id":p.id,"sku":p.sku,"name":p.name,"price":float(p.price),"stock":p.stock_quantity})

@api_bp.get("/reports/sales")
@login_required
def sales_report():
    if current_user.role not in ("admin","employee"):
        return jsonify({"error":"forbidden"}), 403
    total = db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(Order.payment_status=="Successful").scalar()
    return jsonify({"total_sales": float(total), "orders": Order.query.count()})

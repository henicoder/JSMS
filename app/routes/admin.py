from functools import wraps
from datetime import date

from flask import (
    Blueprint,
    render_template,
    request,
    abort,
    jsonify
)

from flask_login import login_required, current_user
from sqlalchemy import func

from ..extensions import db

from ..models import (
    Product,
    Category,
    Customer,
    Order,
    Payment,
    Inventory,
    AuditLog
)

from ..services.inventory_service import sync_inventory

from ..services.inventory_prediction_service import (
    get_inventory_predictions
)


# =========================================================
# ADMIN BLUEPRINT
# =========================================================

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# =========================================================
# STAFF / ADMIN ACCESS CONTROL
# =========================================================

def staff_required(admin_only=False):

    def deco(fn):

        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):

            allowed_roles = (
                ["admin"]
                if admin_only
                else ["admin", "employee"]
            )

            if current_user.role not in allowed_roles:
                abort(403)

            return fn(*args, **kwargs)

        return wrapper

    return deco


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@admin_bp.get("/")
@staff_required()
def dashboard():

    stats = {

        "sales": db.session.query(
            func.coalesce(
                func.sum(Order.total_amount),
                0
            )
        ).filter(
            Order.payment_status == "Successful"
        ).scalar(),

        "orders": Order.query.count(),

        "customers": Customer.query.count(),

        "products": Product.query.count(),

        "low_stock": Product.query.filter(
            Product.stock_quantity <= Product.low_stock_threshold
        ).count(),

        "pending": Order.query.filter(
            Order.order_status == "Pending"
        ).count()
    }

    recent_orders = (
        Order.query
        .order_by(Order.order_date.desc())
        .limit(6)
        .all()
    )

    low_stock = (
        Product.query
        .filter(
            Product.stock_quantity <= Product.low_stock_threshold
        )
        .limit(6)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_orders=recent_orders,
        low_stock=low_stock
    )


# =========================================================
# PRODUCT MANAGEMENT
# =========================================================

@admin_bp.route("/products", methods=["GET", "POST"])
@staff_required()
def products():

    if request.method == "POST":

        # Only admin can add products
        if current_user.role != "admin":
            abort(403)

        category_id = request.form.get(
            "category_id",
            type=int
        )

        category = Category.query.get_or_404(
            category_id
        )

        product = Product(

            sku=request.form["sku"].strip(),

            name=request.form["name"].strip(),

            description=request.form.get(
                "description"
            ),

            price=request.form.get(
                "price",
                type=float
            ),

            metal_type=request.form.get(
                "metal_type"
            ),

            purity=request.form.get(
                "purity"
            ),

            weight=request.form.get(
                "weight",
                type=float
            ) or 0,

            making_charge=request.form.get(
                "making_charge",
                type=float
            ) or 0,

            making_charge_percent=request.form.get(
                "making_charge_percent",
                type=float
            ) or 0,

            gst_rate=request.form.get(
                "gst_rate",
                type=float
            ) or 3,

            stock_quantity=request.form.get(
                "stock_quantity",
                type=int
            ) or 0,

            low_stock_threshold=request.form.get(
                "low_stock_threshold",
                type=int
            ) or 3,

            category=category
        )

        # Check duplicate SKU
        if Product.query.filter_by(
            sku=product.sku
        ).first():

            from flask import flash

            flash(
                "SKU already exists.",
                "danger"
            )

        else:

            db.session.add(product)

            db.session.flush()

            # Keep inventory table synchronized
            sync_inventory(product)

            db.session.commit()

            from flask import flash

            flash(
                "Product added.",
                "success"
            )

    return render_template(
        "admin/products.html",

        products=(
            Product.query
            .order_by(Product.id.desc())
            .all()
        ),

        categories=(
            Category.query
            .order_by(Category.name)
            .all()
        )
    )


# =========================================================
# CATEGORY MANAGEMENT
# =========================================================

@admin_bp.route(
    "/categories",
    methods=["GET", "POST"]
)
@staff_required(admin_only=True)
def categories():

    if request.method == "POST":

        from flask import flash

        name = request.form["name"].strip()

        existing_category = (
            Category.query
            .filter_by(name=name)
            .first()
        )

        if not existing_category:

            db.session.add(
                Category(
                    name=name,
                    description=request.form.get(
                        "description"
                    )
                )
            )

            db.session.commit()

            flash(
                "Category added successfully.",
                "success"
            )

        else:

            flash(
                "Category already exists.",
                "warning"
            )

    return render_template(
        "admin/categories.html",

        categories=(
            Category.query
            .order_by(Category.name)
            .all()
        )
    )


# =========================================================
# INVENTORY PREDICTIONS
# =========================================================

@admin_bp.route("/inventory-predictions")
@staff_required()
def inventory_predictions():

    predictions = get_inventory_predictions(
        days=30,
        lead_time_days=15
    )

    return render_template(
        "admin/inventory-predictions.html",
        predictions=predictions
    )


# =========================================================
# LIVE SALES TRACKER PAGE
# =========================================================

@admin_bp.route("/live-sales")
@staff_required()
def live_sales():

    return render_template(
        "admin/live-sales.html"
    )


# =========================================================
# LIVE SALES API
# =========================================================

@admin_bp.route("/api/live-sales")
@staff_required()
def live_sales_api():

    # -----------------------------------------------------
    # Today's date
    # -----------------------------------------------------

    today = date.today()


    # -----------------------------------------------------
    # Today's orders
    # -----------------------------------------------------

    orders_today = (
        Order.query
        .filter(
            func.date(Order.order_date) == today
        )
        .all()
    )


    # -----------------------------------------------------
    # Today's revenue
    # -----------------------------------------------------

    total_revenue = sum(
        float(order.total_amount or 0)
        for order in orders_today
        if order.payment_status in (
            "Successful",
            "Paid"
        )
    )


    # -----------------------------------------------------
    # Today's order count
    # -----------------------------------------------------

    total_orders = len(
        orders_today
    )


    # -----------------------------------------------------
    # Pending / processing orders
    # -----------------------------------------------------

    pending_orders = (
        Order.query
        .filter(
            Order.order_status.in_(
                [
                    "Pending",
                    "Processing"
                ]
            )
        )
        .count()
    )


    # -----------------------------------------------------
    # Total customers
    # -----------------------------------------------------

    total_customers = (
        Customer.query.count()
    )


    # -----------------------------------------------------
    # Recent orders
    # -----------------------------------------------------

    recent_orders = (
        Order.query
        .order_by(
            Order.order_date.desc()
        )
        .limit(15)
        .all()
    )


    # -----------------------------------------------------
    # Purchase data
    # -----------------------------------------------------

    purchases = []


    for order in recent_orders:

        # Get payment information
        payment = (
            Payment.query
            .filter_by(
                order_id=order.id
            )
            .first()
        )


        # -------------------------------------------------
        # Customer
        # -------------------------------------------------

        customer_name = "Unknown"

        if order.customer:
            customer_name = (
                order.customer.name
            )


        # -------------------------------------------------
        # Order items
        # -------------------------------------------------

        for item in order.items:

            # Calculate item subtotal
            item_subtotal = (
                float(item.unit_price or 0)
                * item.quantity
            )


            # Calculate item making charge
            item_making_charge = (
                float(item.making_charge or 0)
                * item.quantity
            )


            # Calculate GST
            taxable_amount = (
                item_subtotal
                + item_making_charge
            )

            item_gst = (
                taxable_amount
                * float(item.gst_rate or 0)
                / 100
            )


            # Final item amount
            item_total = (
                taxable_amount
                + item_gst
            )


            purchases.append({

                "order_number":
                    order.order_number,

                "customer":
                    customer_name,

                "product":
                    item.product_name,

                "sku":
                    item.sku,

                "quantity":
                    item.quantity,

                "amount":
                    round(item_total, 2),

                "payment_method":
                    (
                        payment.payment_method
                        if payment
                        else "N/A"
                    ),

                "payment_status":
                    (
                        payment.payment_status
                        if payment
                        else order.payment_status
                    ),

                "order_status":
                    order.order_status,

                "date":
                    (
                        order.order_date
                        .strftime("%d %b %Y")
                        if order.order_date
                        else ""
                    ),

                "time":
                    (
                        order.order_date
                        .strftime("%I:%M:%S %p")
                        if order.order_date
                        else ""
                    )
            })


    # -----------------------------------------------------
    # Return JSON
    # -----------------------------------------------------

    return jsonify({

        "success": True,

        "stats": {

            "revenue_today":
                round(
                    total_revenue,
                    2
                ),

            "orders_today":
                total_orders,

            "total_customers":
                total_customers,

            "pending_orders":
                pending_orders
        },

        "purchases":
            purchases

    })
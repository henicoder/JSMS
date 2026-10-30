from decimal import Decimal
from uuid import uuid4

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    flash,
    redirect,
    url_for
)

from flask_login import login_required, current_user

from ..extensions import db

from ..models import (
    Product,
    Category,
    Order,
    OrderItem,
    Customer,
    CustomJewellery
)

from ..services.recommendation_service import recommend_products

from ..services.metal_price_service import (
    get_metal_prices
)

from ..services.custom_jewellery_service import (
    calculate_custom_jewellery
)


main_bp = Blueprint("main", __name__)


# ============================================================
# HOME
# ============================================================

@main_bp.get("/")
def home():

    # --------------------------------------------------------
    # Latest active products
    # --------------------------------------------------------

    products = (
        Product.query
        .filter_by(status="active")
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )

    # --------------------------------------------------------
    # Active categories
    # --------------------------------------------------------

    categories = (
        Category.query
        .filter_by(active=True)
        .all()
    )

    # --------------------------------------------------------
    # LUMIÈRE AI PERSONALIZED RECOMMENDATIONS
    # --------------------------------------------------------

    ai_recommendations = []
    ai_message = ""

    if current_user.is_authenticated:

        # IMPORTANT:
        # current_user.id is the User ID.
        # Customer has its own ID.

        customer = Customer.query.filter_by(
            user_id=current_user.id
        ).first()

        if customer:

            # ------------------------------------------------
            # Get all active products
            # ------------------------------------------------

            all_products = (
                Product.query
                .filter_by(status="active")
                .all()
            )

            # ------------------------------------------------
            # Use the existing recommendation engine
            # ------------------------------------------------
            # We slice the result here instead of passing
            # limit=3 because recommendation_service.py
            # currently does not accept a limit parameter.

            ai_recommendations = recommend_products(
                products=all_products
            )[:3]

            # ------------------------------------------------
            # Generate personalized AI message
            # ------------------------------------------------

            if ai_recommendations:

                first_product = (
                    ai_recommendations[0]["product"]
                )

                reasons = (
                    ai_recommendations[0]["reasons"]
                )

                if reasons:

                    reason_text = reasons[0].lower()

                    ai_message = (
                        f"Welcome back, {customer.name}! "
                        f"I found something you might love. "
                        f"Our {first_product.name} "
                        f"{reason_text}. "
                        f"Take a look at this special recommendation "
                        f"from Shree Vagheswari Jewellers AI."
                    )

                else:

                    ai_message = (
                        f"Welcome back, {customer.name}! "
                        f"I found a jewellery piece you might love: "
                        f"{first_product.name}. "
                        f"Take a look at your personalized "
                        f"Shree Vagheswari Jewellers AI recommendations."
                    )

            else:

                ai_message = (
                    f"Welcome back, {customer.name}! "
                    f"I'm currently looking for the perfect "
                    f"jewellery pieces for you."
                )

    # --------------------------------------------------------
    # Render Home
    # --------------------------------------------------------

    return render_template(
        "home.html",
        products=products,
        categories=categories,
        ai_recommendations=ai_recommendations,
        ai_message=ai_message
    )


# ============================================================
# SHOP
# ============================================================

@main_bp.route("/shop")
def shop():

    q = request.args.get(
        "q",
        ""
    ).strip()

    category_id = request.args.get(
        "category",
        type=int
    )

    query = Product.query.filter_by(
        status="active"
    )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    if q:

        query = query.filter(
            db.or_(
                Product.name.ilike(
                    f"%{q}%"
                ),
                Product.sku.ilike(
                    f"%{q}%"
                ),
                Product.metal_type.ilike(
                    f"%{q}%"
                )
            )
        )

    # --------------------------------------------------------
    # Category filter
    # --------------------------------------------------------

    if category_id:

        query = query.filter_by(
            category_id=category_id
        )

    # --------------------------------------------------------
    # Products
    # --------------------------------------------------------

    products = (
        query
        .order_by(Product.created_at.desc())
        .all()
    )

    # --------------------------------------------------------
    # Categories
    # --------------------------------------------------------

    categories = (
        Category.query
        .filter_by(active=True)
        .all()
    )

    return render_template(
        "shop.html",
        products=products,
        categories=categories
    )


# ============================================================
# AI JEWELLERY RECOMMENDATIONS
# ============================================================

@main_bp.route(
    "/recommendations",
    methods=["GET", "POST"]
)
def recommendations():

    recommendations = []
    submitted = False

    if request.method == "POST":

        submitted = True

        # ----------------------------------------------------
        # Get user preferences
        # ----------------------------------------------------

        occasion = request.form.get(
            "occasion",
            ""
        ).strip()

        jewellery_type = request.form.get(
            "jewellery_type",
            ""
        ).strip()

        budget = request.form.get(
            "budget",
            ""
        ).strip()

        metal = request.form.get(
            "metal",
            ""
        ).strip()

        purity = request.form.get(
            "purity",
            ""
        ).strip()

        style = request.form.get(
            "style",
            ""
        ).strip()

        # ----------------------------------------------------
        # Get active products
        # ----------------------------------------------------

        products = (
            Product.query
            .filter_by(status="active")
            .all()
        )

        # ----------------------------------------------------
        # Generate recommendations
        # ----------------------------------------------------
        # recommendation_service.py currently returns
        # a maximum of 8 products, so we slice here as well.

        recommendations = recommend_products(
            products=products,
            occasion=occasion,
            jewellery_type=jewellery_type,
            budget=budget,
            metal=metal,
            purity=purity,
            style=style
        )[:8]

    return render_template(
        "recommendations.html",
        recommendations=recommendations,
        submitted=submitted
    )


# ============================================================
# BUILD YOUR JEWELLERY SET
# ============================================================

@main_bp.route("/build-set")
@login_required
def build_set():

    products = (
        Product.query
        .filter_by(status="active")
        .all()
    )

    return render_template(
        "build_set.html",
        products=products
    )


# ============================================================
# BUILD SET - PRODUCT CALCULATION
# ============================================================

@main_bp.route(
    "/api/build_set/calculate",
    methods=["POST"]
)
def calculate_build_set():

    data = request.get_json() or {}

    product_ids = data.get(
        "product_ids",
        []
    )

    # --------------------------------------------------------
    # No products selected
    # --------------------------------------------------------

    if not product_ids:

        return jsonify({
            "success": True,
            "items": [],
            "subtotal": 0,
            "making_charges": 0,
            "gst": 0,
            "total": 0
        })

    # --------------------------------------------------------
    # Validate product IDs
    # --------------------------------------------------------

    try:

        product_ids = [
            int(pid)
            for pid in product_ids
        ]

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "error": "Invalid product selection."
        }), 400

    # --------------------------------------------------------
    # Get selected active products
    # --------------------------------------------------------

    products = (
        Product.query
        .filter(
            Product.id.in_(product_ids),
            Product.status == "active"
        )
        .all()
    )

    # --------------------------------------------------------
    # Check unavailable products
    # --------------------------------------------------------

    if len(products) != len(set(product_ids)):

        return jsonify({
            "success": False,
            "error": (
                "One or more selected products "
                "are unavailable."
            )
        }), 400

    items = []

    subtotal = Decimal("0")
    making_charges = Decimal("0")
    gst = Decimal("0")

    # --------------------------------------------------------
    # Calculate every product
    # --------------------------------------------------------

    for product in products:

        # ----------------------------------------------------
        # Check stock
        # ----------------------------------------------------

        if (product.stock_quantity or 0) <= 0:

            return jsonify({
                "success": False,
                "error": (
                    f"{product.name} "
                    "is currently out of stock."
                )
            }), 400

        # ----------------------------------------------------
        # Product price
        # ----------------------------------------------------

        price = Decimal(
            str(product.price or 0)
        )

        # ----------------------------------------------------
        # Fixed making charge
        # ----------------------------------------------------

        making = Decimal(
            str(product.making_charge or 0)
        )

        # ----------------------------------------------------
        # Percentage making charge
        # ----------------------------------------------------

        if product.making_charge_percent:

            making += (
                price
                * Decimal(
                    str(
                        product.making_charge_percent
                    )
                )
                / Decimal("100")
            )

        # ----------------------------------------------------
        # Taxable amount
        # ----------------------------------------------------

        taxable = price + making

        # ----------------------------------------------------
        # GST
        # ----------------------------------------------------

        item_gst = (
            taxable
            * Decimal(
                str(product.gst_rate or 0)
            )
            / Decimal("100")
        )

        # ----------------------------------------------------
        # Add totals
        # ----------------------------------------------------

        subtotal += price
        making_charges += making
        gst += item_gst

        # ----------------------------------------------------
        # Add item information
        # ----------------------------------------------------

        items.append({
            "id": product.id,
            "name": product.name,
            "price": float(price),
            "making_charge": float(making),
            "gst": float(item_gst),
            "stock": product.stock_quantity
        })

    # --------------------------------------------------------
    # Final total
    # --------------------------------------------------------

    total = (
        subtotal
        + making_charges
        + gst
    )

    return jsonify({
        "success": True,
        "items": items,
        "subtotal": float(subtotal),
        "making_charges": float(making_charges),
        "gst": float(gst),
        "total": float(total)
    })


# ============================================================
# SILVER PRICE INTELLIGENCE
# ============================================================

@main_bp.route("/metal_prices")
def metal_prices():

    from ..services.metal_price_service import (
        calculate_metal_value
    )

    # --------------------------------------------------------
    # Active products
    # --------------------------------------------------------

    products = (
        Product.query
        .filter_by(status="active")
        .all()
    )

    # --------------------------------------------------------
    # Calculate metal value
    # --------------------------------------------------------

    for product in products:

        product.metal_value = calculate_metal_value(
            product.metal_type,
            product.purity,
            product.weight
        )

    # --------------------------------------------------------
    # Get current metal prices
    # --------------------------------------------------------

    prices = get_metal_prices()

    return render_template(
        "metal_price.html",
        prices=prices,
        products=products
    )


# ============================================================
# CUSTOM JEWELLERY - PRICE CALCULATION API
# ============================================================

@main_bp.route(
    "/api/custom-jewellery/calculate",
    methods=["POST"]
)
@login_required
def calculate_custom_jewellery_api():

    data = request.get_json() or {}

    try:

        # ----------------------------------------------------
        # Get weight
        # ----------------------------------------------------

        weight = float(
            data.get(
                "weight",
                0
            )
        )

        # ----------------------------------------------------
        # Validate weight
        # ----------------------------------------------------

        if weight <= 0:

            return jsonify({
                "success": False,
                "error": (
                    "Weight must be greater than 0."
                )
            }), 400

        # ----------------------------------------------------
        # Get making charge
        # ----------------------------------------------------

        making_charge = float(
            data.get(
                "making_charge",
                0
            )
        )

        # ----------------------------------------------------
        # Get customization charge
        # ----------------------------------------------------

        customization_charge = float(
            data.get(
                "customization_charge",
                0
            )
        )

        # ----------------------------------------------------
        # Calculate using current silver price
        # ----------------------------------------------------

        result = calculate_custom_jewellery(
            weight,
            making_charge,
            customization_charge
        )

        return jsonify({
            "success": True,
            "silver_rate": float(
                result["silver_rate"]
            ),
            "silver_value": float(
                result["silver_value"]
            ),
            "making_charge": float(
                result["making_charge"]
            ),
            "customization_charge": float(
                result["customization_charge"]
            ),
            "gst": float(
                result["gst"]
            ),
            "final_amount": float(
                result["final_amount"]
            )
        })

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "error": (
                "Please enter valid values."
            )
        }), 400


# ============================================================
# CUSTOM JEWELLERY - CREATE ORDER
# ============================================================

@main_bp.route(
    "/custom-jewellery/order",
    methods=["POST"]
)
@login_required
def create_custom_jewellery_order():

    try:

        # ----------------------------------------------------
        # IMPORTANT:
        # current_user.id is the User ID.
        # Customer has its own ID.
        # ----------------------------------------------------

        customer = Customer.query.filter_by(
            user_id=current_user.id
        ).first()

        if not customer:

            flash(
                "Customer profile not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "main.build_set"
                )
            )

        # ----------------------------------------------------
        # Jewellery type
        # ----------------------------------------------------

        jewellery_type = request.form.get(
            "jewellery_type",
            "Ring"
        ).strip()

        # ----------------------------------------------------
        # Design style
        # ----------------------------------------------------

        design_style = request.form.get(
            "design_style",
            "Minimal"
        ).strip()

        # ----------------------------------------------------
        # Weight
        # ----------------------------------------------------

        weight = float(
            request.form.get(
                "weight",
                0
            )
        )

        # ----------------------------------------------------
        # Size / length
        # ----------------------------------------------------

        size = request.form.get(
            "size",
            ""
        ).strip()

        # ----------------------------------------------------
        # Finish
        # ----------------------------------------------------

        finish = request.form.get(
            "finish",
            "Polished"
        ).strip()

        # ----------------------------------------------------
        # Engraving
        # ----------------------------------------------------

        engraving = request.form.get(
            "engraving",
            ""
        ).strip()

        # ----------------------------------------------------
        # Making charge
        # ----------------------------------------------------

        making_charge = float(
            request.form.get(
                "making_charge",
                0
            )
        )

        # ----------------------------------------------------
        # Customization charge
        # ----------------------------------------------------

        customization_charge = float(
            request.form.get(
                "customization_charge",
                0
            )
        )

        # ----------------------------------------------------
        # Validate weight
        # ----------------------------------------------------

        if weight <= 0:

            flash(
                "Please enter a valid jewellery weight.",
                "danger"
            )

            return redirect(
                url_for(
                    "main.build_set"
                )
            )

        # ----------------------------------------------------
        # Validate charges
        # ----------------------------------------------------

        if making_charge < 0:

            flash(
                "Invalid making charge.",
                "danger"
            )

            return redirect(
                url_for(
                    "main.build_set"
                )
            )

        if customization_charge < 0:

            flash(
                "Invalid customization charge.",
                "danger"
            )

            return redirect(
                url_for(
                    "main.build_set"
                )
            )

        # ====================================================
        # Calculate the price again at actual order time
        # ====================================================

        result = calculate_custom_jewellery(
            weight,
            making_charge,
            customization_charge
        )

        # ====================================================
        # Create CustomJewellery record
        # ====================================================

        custom_order = CustomJewellery(
            customer_id=customer.id,
            jewellery_type=jewellery_type,
            design_style=design_style,
            silver_purity="925",
            weight=weight,
            size=size,
            finish=finish,
            engraving=engraving,
            silver_rate_at_purchase=(
                result["silver_rate"]
            ),
            silver_value=(
                result["silver_value"]
            ),
            making_charge=(
                result["making_charge"]
            ),
            customization_charge=(
                result["customization_charge"]
            ),
            gst=(
                result["gst"]
            ),
            final_amount=(
                result["final_amount"]
            ),
            status="Pending"
        )

        db.session.add(custom_order)

        # ----------------------------------------------------
        # Flush to get CustomJewellery ID
        # ----------------------------------------------------

        db.session.flush()

        # ====================================================
        # Create normal Order record
        # ====================================================

        order_number = (
            f"CUSTOM-{uuid4().hex[:12].upper()}"
        )

        # ----------------------------------------------------
        # Build shipping address
        # ----------------------------------------------------

        address_parts = []

        if customer.address:
            address_parts.append(
                customer.address.strip()
            )

        if customer.city:
            address_parts.append(
                customer.city.strip()
            )

        if customer.state:
            address_parts.append(
                customer.state.strip()
            )

        if customer.pincode:
            address_parts.append(
                customer.pincode.strip()
            )

        shipping_address = ", ".join(
            part
            for part in address_parts
            if part
        )

        # ----------------------------------------------------
        # Convert calculation values to Decimal
        # ----------------------------------------------------

        silver_value = Decimal(
            str(result["silver_value"])
        )

        making_charge_amount = Decimal(
            str(result["making_charge"])
        )

        customization_charge_amount = Decimal(
            str(result["customization_charge"])
        )

        gst_amount = Decimal(
            str(result["gst"])
        )

        final_amount = Decimal(
            str(result["final_amount"])
        )

        # ----------------------------------------------------
        # Create Order
        # ----------------------------------------------------

        order = Order(
            order_number=order_number,
            customer_id=customer.id,
            subtotal=silver_value,
            making_charges=(
                making_charge_amount
                + customization_charge_amount
            ),
            discount=Decimal("0"),
            gst=gst_amount,
            total_amount=final_amount,
            payment_status="Pending",
            order_status="Pending",
            shipping_address=shipping_address
        )

        db.session.add(order)

        # ----------------------------------------------------
        # Flush to get Order ID
        # ----------------------------------------------------

        db.session.flush()

        # ====================================================
        # Connect CustomJewellery to Order
        # ====================================================

        custom_order.order_id = order.id

        # ====================================================
        # Create OrderItem
        # ====================================================
        #
        # This is a custom product, so:
        #
        # product_id = None
        #
        # The actual custom jewellery details remain stored
        # in CustomJewellery.
        # ====================================================

        custom_item = OrderItem(
            order_id=order.id,
            product_id=None,
            product_name=(
                f"Custom Shree Vagheswari Jewellers "
                f"{jewellery_type}"
            ),
            sku=(
                f"CUSTOM-{custom_order.id}"
            ),
            quantity=1,
            unit_price=silver_value,
            making_charge=making_charge_amount,
            customization_charge=(
                customization_charge_amount
            ),
            gst_rate=Decimal("3"),
            gst_amount=gst_amount
        )

        db.session.add(custom_item)

        # ====================================================
        # Commit everything together
        # ====================================================

        db.session.commit()

        # ----------------------------------------------------
        # Success message
        # ----------------------------------------------------

        flash(
            f"Custom jewellery order "
            f"#{order.order_number} "
            f"created successfully!",
            "success"
        )

        # ----------------------------------------------------
        # Redirect to build set
        # ----------------------------------------------------

        return redirect(
            url_for(
                "main.build_set"
            )
        )

    except (ValueError, TypeError):

        db.session.rollback()

        flash(
            "Please enter valid customization details.",
            "danger"
        )

        return redirect(
            url_for(
                "main.build_set"
            )
        )

    except Exception:

        db.session.rollback()

        flash(
            "Unable to create your custom jewellery order. "
            "Please try again.",
            "danger"
        )

        return redirect(
            url_for(
                "main.build_set"
            )
        )
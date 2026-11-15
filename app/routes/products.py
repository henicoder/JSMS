from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    session
)

from flask_login import login_required, current_user

from datetime import datetime
from decimal import Decimal, InvalidOperation
import uuid
import traceback

from ..extensions import db

from ..models import (
    Product,
    Customer,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Payment,
    Invoice,
    Wishlist
)

from ..services.inventory_service import change_stock
from ..services.billing_service import calculate_item


products_bp = Blueprint(
    "products",
    __name__
)


# ============================================================
# PRODUCT LISTING
# ============================================================

@products_bp.route("/")
def index():

    category_name = request.args.get(
        "category",
        ""
    ).strip()

    query = Product.query.filter_by(
        status="active"
    )

    if category_name:
        query = query.filter(
            Product.category.has(
                name=category_name
            )
        )

    products = query.all()

    # --------------------------------------------------------
    # Wishlist products for logged-in customer
    # --------------------------------------------------------

    wishlist_product_ids = set()

    if current_user.is_authenticated:

        customer = Customer.query.filter_by(
            user_id=current_user.id
        ).first()

        if customer:

            wishlist_product_ids = {
                item.product_id
                for item in Wishlist.query.filter_by(
                    customer_id=customer.id
                ).all()
            }

    return render_template(
        "shop.html",
        products=products,
        selected_category=category_name,
        wishlist_product_ids=wishlist_product_ids
    )


# ============================================================
# PRODUCT DETAILS
# ============================================================

@products_bp.route("/<int:product_id>")
def detail(product_id):

    product = Product.query.get_or_404(
        product_id
    )

    return render_template(
        "product-details.html",
        product=product
    )


# ============================================================
# PRODUCT API
# ============================================================

@products_bp.route("/api/<int:product_id>")
def product_api(product_id):

    product = Product.query.get_or_404(
        product_id
    )

    return jsonify({
        "id": product.id,

        "name": product.name,

        "sku": product.sku,

        "price": float(
            product.price or 0
        ),

        "discount_percent": float(
            getattr(
                product,
                "discount_percent",
                0
            ) or 0
        ),

        "making_charge": float(
            product.making_charge or 0
        ),

        "making_charge_percent": float(
            product.making_charge_percent or 0
        ),

        "gst_rate": float(
            product.gst_rate or 0
        ),

        "stock_quantity": int(
            product.stock_quantity or 0
        ),

        "category": (
            product.category.name
            if product.category
            else "Jewellery"
        )
    })


# ============================================================
# ADD PRODUCT TO CART
# ============================================================

@products_bp.route(
    "/api/<int:product_id>/add-to-cart",
    methods=["POST"]
)
@login_required
def add_to_cart(product_id):

    product = Product.query.get_or_404(
        product_id
    )

    # --------------------------------------------------------
    # Product status
    # --------------------------------------------------------

    if product.status != "active":

        return jsonify({
            "success": False,
            "message": "This product is not available."
        }), 400

    # --------------------------------------------------------
    # Stock check
    # --------------------------------------------------------

    stock = int(
        product.stock_quantity or 0
    )

    if stock <= 0:

        return jsonify({
            "success": False,
            "message": "This product is out of stock."
        }), 400

    # --------------------------------------------------------
    # Find Customer
    # --------------------------------------------------------

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        return jsonify({
            "success": False,
            "message": "Customer profile not found."
        }), 400

    # --------------------------------------------------------
    # Find cart
    # --------------------------------------------------------

    cart = Cart.query.filter_by(
        customer_id=customer.id
    ).first()

    # --------------------------------------------------------
    # Create cart
    # --------------------------------------------------------

    if not cart:

        cart = Cart(
            customer_id=customer.id
        )

        db.session.add(cart)
        db.session.flush()

    # --------------------------------------------------------
    # Existing cart item
    # --------------------------------------------------------

    cart_item = CartItem.query.filter_by(
        cart_id=cart.id,
        product_id=product.id
    ).first()

    if cart_item:

        current_quantity = int(
            cart_item.quantity or 0
        )

        if current_quantity >= stock:

            return jsonify({
                "success": False,
                "message": (
                    "Maximum available stock "
                    "already added to your cart."
                )
            }), 400

        cart_item.quantity = (
            current_quantity + 1
        )

    else:

        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=1
        )

        db.session.add(
            cart_item
        )

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Unable to add product to cart."
        }), 500

    flash(
        f"{product.name} added to your cart successfully.",
        "success"
    )

    return redirect(
        url_for("products.cart")
    )


# ============================================================
# VIEW CART
# ============================================================

@products_bp.route("/cart")
@login_required
def cart():

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        return render_template(
            "cart.html",
            cart=None,
            items=[],
            subtotal=0,
            discount=0,
            making_charges=0,
            gst=0,
            total=0
        )

    cart = Cart.query.filter_by(
        customer_id=customer.id
    ).first()

    if not cart:

        return render_template(
            "cart.html",
            cart=None,
            items=[],
            subtotal=0,
            discount=0,
            making_charges=0,
            gst=0,
            total=0
        )

    items = cart.items

    subtotal = Decimal("0")
    discount = Decimal("0")
    making_charges = Decimal("0")
    gst = Decimal("0")

    # --------------------------------------------------------
    # Calculate every cart item
    # --------------------------------------------------------

    for item in items:

        product = item.product

        if not product:
            continue

        quantity = int(
            item.quantity or 0
        )

        calculation = calculate_item(
            product,
            quantity
        )

        item.subtotal = float(
            calculation.get(
                "base",
                0
            )
        )

        item.discount_percent = float(
            calculation.get(
                "discount_percent",
                0
            )
        )

        item.discount_total = float(
            calculation.get(
                "discount",
                0
            )
        )

        item.discounted_subtotal = float(
            calculation.get(
                "discounted_base",
                calculation.get(
                    "base",
                    0
                )
            )
        )

        item.making_total = float(
            calculation.get(
                "making",
                0
            )
        )

        item.gst_total = float(
            calculation.get(
                "gst",
                0
            )
        )

        item.total = float(
            calculation.get(
                "total",
                0
            )
        )

        subtotal += Decimal(
            str(
                calculation.get(
                    "base",
                    0
                )
            )
        )

        discount += Decimal(
            str(
                calculation.get(
                    "discount",
                    0
                )
            )
        )

        making_charges += Decimal(
            str(
                calculation.get(
                    "making",
                    0
                )
            )
        )

        gst += Decimal(
            str(
                calculation.get(
                    "gst",
                    0
                )
            )
        )

    total = (
        subtotal
        - discount
        + making_charges
        + gst
    )

    return render_template(
        "cart.html",
        cart=cart,
        items=items,
        subtotal=float(subtotal),
        discount=float(discount),
        making_charges=float(making_charges),
        gst=float(gst),
        total=float(total)
    )


# ============================================================
# UPDATE CART QUANTITY
# ============================================================

@products_bp.route(
    "/cart/update/<int:item_id>",
    methods=["POST"]
)
@login_required
def update_cart_item(item_id):

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        return jsonify({
            "success": False,
            "message": "Customer profile not found."
        }), 400

    item = CartItem.query.get_or_404(
        item_id
    )

    if not item.cart:

        return jsonify({
            "success": False,
            "message": "Cart not found."
        }), 404

    # --------------------------------------------------------
    # Security check
    # --------------------------------------------------------

    if item.cart.customer_id != customer.id:

        return jsonify({
            "success": False,
            "message": "Unauthorized cart item."
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    try:

        quantity = int(
            data.get(
                "quantity",
                1
            )
        )

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Invalid quantity."
        }), 400

    # --------------------------------------------------------
    # Remove item
    # --------------------------------------------------------

    if quantity <= 0:

        try:

            db.session.delete(item)
            db.session.commit()

        except Exception:

            db.session.rollback()

            traceback.print_exc()

            return jsonify({
                "success": False,
                "message": "Unable to remove item."
            }), 500

        return jsonify({
            "success": True,
            "removed": True,
            "message": "Item removed from cart."
        })

    # --------------------------------------------------------
    # Product check
    # --------------------------------------------------------

    if not item.product:

        return jsonify({
            "success": False,
            "message": "Product no longer exists."
        }), 400

    # --------------------------------------------------------
    # Stock check
    # --------------------------------------------------------

    available_stock = int(
        item.product.stock_quantity or 0
    )

    if quantity > available_stock:

        return jsonify({
            "success": False,
            "message": (
                f"Only {available_stock} "
                "item(s) available."
            )
        }), 400

    item.quantity = quantity

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Unable to update cart."
        }), 500

    return jsonify({
        "success": True,
        "removed": False,
        "quantity": item.quantity,
        "message": "Cart updated successfully."
    })


# ============================================================
# REMOVE CART ITEM
# ============================================================

@products_bp.route(
    "/cart/remove/<int:item_id>",
    methods=["POST"]
)
@login_required
def remove_cart_item(item_id):

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        return jsonify({
            "success": False,
            "message": "Customer profile not found."
        }), 400

    item = CartItem.query.get_or_404(
        item_id
    )

    if not item.cart:

        return jsonify({
            "success": False,
            "message": "Cart not found."
        }), 404

    # --------------------------------------------------------
    # Security check
    # --------------------------------------------------------

    if item.cart.customer_id != customer.id:

        return jsonify({
            "success": False,
            "message": "Unauthorized cart item."
        }), 403

    try:

        db.session.delete(item)
        db.session.commit()

    except Exception:

        db.session.rollback()

        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": "Unable to remove item."
        }), 500

    return jsonify({
        "success": True,
        "message": "Item removed from cart."
    })


# ============================================================
# CHECKOUT
# ============================================================

@products_bp.route(
    "/checkout",
    methods=["GET", "POST"]
)
@login_required
def checkout():

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        flash(
            "Customer profile not found.",
            "danger"
        )

        return redirect(
            url_for("products.cart")
        )

    cart = Cart.query.filter_by(
        customer_id=customer.id
    ).first()

    if not cart or not cart.items:

        flash(
            "Your cart is empty.",
            "warning"
        )

        return redirect(
            url_for("products.cart")
        )

    items = cart.items

    subtotal = Decimal("0")
    discount = Decimal("0")
    making_charges = Decimal("0")
    gst = Decimal("0")

    # --------------------------------------------------------
    # Calculate using billing service
    # --------------------------------------------------------

    for item in items:

        product = item.product

        if not product:

            flash(
                "One of the products in your cart is no longer available.",
                "danger"
            )

            return redirect(
                url_for("products.cart")
            )

        quantity = int(
            item.quantity or 0
        )

        calculation = calculate_item(
            product,
            quantity
        )

        item.subtotal = float(
            calculation.get("base", 0)
        )

        item.discount_percent = float(
            calculation.get(
                "discount_percent",
                0
            )
        )

        item.discount_total = float(
            calculation.get(
                "discount",
                0
            )
        )

        item.discounted_subtotal = float(
            calculation.get(
                "discounted_base",
                calculation.get(
                    "base",
                    0
                )
            )
        )

        item.making_total = float(
            calculation.get(
                "making",
                0
            )
        )

        item.gst_total = float(
            calculation.get(
                "gst",
                0
            )
        )

        item.total = float(
            calculation.get(
                "total",
                0
            )
        )

        subtotal += Decimal(
            str(
                calculation.get(
                    "base",
                    0
                )
            )
        )

        discount += Decimal(
            str(
                calculation.get(
                    "discount",
                    0
                )
            )
        )

        making_charges += Decimal(
            str(
                calculation.get(
                    "making",
                    0
                )
            )
        )

        gst += Decimal(
            str(
                calculation.get(
                    "gst",
                    0
                )
            )
        )

    total = (
        subtotal
        - discount
        + making_charges
        + gst
    )

    # --------------------------------------------------------
    # Save customer details
    # --------------------------------------------------------

    if request.method == "POST":

        customer.name = request.form.get(
            "name",
            ""
        ).strip()

        customer.email = request.form.get(
            "email",
            ""
        ).strip().lower()

        customer.phone = request.form.get(
            "phone",
            ""
        ).strip()

        customer.address = request.form.get(
            "address",
            ""
        ).strip()

        customer.city = request.form.get(
            "city",
            ""
        ).strip()

        customer.state = request.form.get(
            "state",
            ""
        ).strip()

        customer.pincode = request.form.get(
            "pincode",
            ""
        ).strip()

        if not customer.name:

            flash(
                "Please enter your name.",
                "danger"
            )

            return redirect(
                url_for("products.checkout")
            )

        if not customer.email:

            flash(
                "Please enter your email.",
                "danger"
            )

            return redirect(
                url_for("products.checkout")
            )

        if not customer.address:

            flash(
                "Please enter your delivery address.",
                "danger"
            )

            return redirect(
                url_for("products.checkout")
            )

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            traceback.print_exc()

            flash(
                "Unable to save customer details.",
                "danger"
            )

            return redirect(
                url_for("products.checkout")
            )

        session["checkout_address"] = {
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "address": customer.address,
            "city": customer.city,
            "state": customer.state,
            "pincode": customer.pincode
        }

        return redirect(
            url_for("products.payment")
        )

    return render_template(
        "checkout.html",
        customer=customer,
        items=items,
        subtotal=float(subtotal),
        discount=float(discount),
        making_charges=float(making_charges),
        gst=float(gst),
        total=float(total)
    )


# ============================================================
# PAYMENT
# ============================================================

@products_bp.route(
    "/payment",
    methods=["GET", "POST"]
)
@login_required
def payment():

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        flash(
            "Customer profile not found.",
            "danger"
        )

        return redirect(
            url_for("products.cart")
        )

    cart = Cart.query.filter_by(
        customer_id=customer.id
    ).first()

    if not cart or not cart.items:

        flash(
            "Your cart is empty.",
            "warning"
        )

        return redirect(
            url_for("products.cart")
        )

    items = cart.items

    subtotal = Decimal("0")
    discount = Decimal("0")
    making_charges = Decimal("0")
    gst = Decimal("0")

    # ========================================================
    # CALCULATE ORDER TOTAL
    # ========================================================

    for item in items:

        product = item.product

        if not product:

            flash(
                "One of the products in your cart is no longer available.",
                "danger"
            )

            return redirect(
                url_for("products.cart")
            )

        quantity = int(
            item.quantity or 0
        )

        if quantity <= 0:

            flash(
                "Invalid product quantity.",
                "danger"
            )

            return redirect(
                url_for("products.cart")
            )

        calculation = calculate_item(
            product,
            quantity
        )

        subtotal += Decimal(
            str(
                calculation.get(
                    "base",
                    0
                )
            )
        )

        discount += Decimal(
            str(
                calculation.get(
                    "discount",
                    0
                )
            )
        )

        making_charges += Decimal(
            str(
                calculation.get(
                    "making",
                    0
                )
            )
        )

        gst += Decimal(
            str(
                calculation.get(
                    "gst",
                    0
                )
            )
        )

    total = (
        subtotal
        - discount
        + making_charges
        + gst
    )

    # ========================================================
    # PLACE ORDER
    # ========================================================

    if request.method == "POST":

        payment_method = request.form.get(
            "payment_method",
            ""
        ).strip()

        # ----------------------------------------------------
        # Validate payment method
        # ----------------------------------------------------

        if payment_method not in (
            "UPI",
            "Card",
            "COD"
        ):

            flash(
                "Please select a valid payment method.",
                "warning"
            )

            return redirect(
                url_for("products.payment")
            )

        # ====================================================
        # CHECK STOCK AGAIN
        # ====================================================

        for item in items:

            product = item.product

            if not product:

                flash(
                    "One of the products is no longer available.",
                    "danger"
                )

                return redirect(
                    url_for("products.cart")
                )

            available_stock = int(
                product.stock_quantity or 0
            )

            required_quantity = int(
                item.quantity or 0
            )

            if available_stock < required_quantity:

                flash(
                    f"Sorry, {product.name} "
                    "does not have enough stock.",
                    "danger"
                )

                return redirect(
                    url_for("products.cart")
                )

        # ====================================================
        # DATABASE TRANSACTION
        # ====================================================

        try:

            # ------------------------------------------------
            # Generate Order Number
            # ------------------------------------------------

            order_number = (
                "JSMS-"
                + datetime.now().strftime(
                    "%Y%m%d%H%M%S"
                )
                + "-"
                + uuid.uuid4().hex[:4].upper()
            )

            # ------------------------------------------------
            # Shipping Address
            # ------------------------------------------------

            shipping_address = ", ".join(
                filter(
                    None,
                    [
                        customer.name,
                        customer.address,
                        customer.city,
                        customer.state,
                        customer.pincode
                    ]
                )
            )

            # ------------------------------------------------
            # Payment Status
            # ------------------------------------------------

            if payment_method in (
                "UPI",
                "Card"
            ):

                payment_status = "Paid"
                order_status = "Confirmed"

            else:

                payment_status = "Pending"
                order_status = "Pending"

            # =================================================
            # CREATE ORDER
            # =================================================

            order = Order(

                order_number=order_number,

                customer_id=customer.id,

                subtotal=subtotal,

                making_charges=making_charges,

                discount=discount,

                gst=gst,

                total_amount=total,

                payment_status=payment_status,

                order_status=order_status,

                shipping_address=shipping_address
            )

            db.session.add(order)

            # Get generated order ID
            db.session.flush()

            # Safety check
            if not order.id:

                raise RuntimeError(
                    "Order ID was not generated."
                )

            # =================================================
            # CREATE ORDER ITEMS
            # =================================================

            for cart_item in items:

                product = cart_item.product

                if not product:

                    raise ValueError(
                        "A product in the cart no longer exists."
                    )

                quantity = int(
                    cart_item.quantity or 0
                )

                if quantity <= 0:

                    raise ValueError(
                        "Invalid cart quantity."
                    )

                # -------------------------------------------------
                # Recalculate pricing at order creation
                # -------------------------------------------------

                calculation = calculate_item(
                    product,
                    quantity
                )

                base = Decimal(
                    str(
                        calculation.get(
                            "base",
                            0
                        )
                    )
                )

                item_discount = Decimal(
                    str(
                        calculation.get(
                            "discount",
                            0
                        )
                    )
                )

                discounted_base = Decimal(
                    str(
                        calculation.get(
                            "discounted_base",
                            base - item_discount
                        )
                    )
                )

                item_making_charge = Decimal(
                    str(
                        calculation.get(
                            "making",
                            0
                        )
                    )
                )

                item_gst = Decimal(
                    str(
                        calculation.get(
                            "gst",
                            0
                        )
                    )
                )

                # -------------------------------------------------
                # Discounted Unit Price
                # -------------------------------------------------

                discounted_unit_price = (
                    discounted_base
                    / Decimal(quantity)
                )

                # =================================================
                # CREATE ORDER ITEM
                # =================================================

                order_item = OrderItem(

                    order_id=order.id,

                    product_id=product.id,

                    product_name=product.name,

                    sku=product.sku,

                    quantity=quantity,

                    unit_price=discounted_unit_price,

                    making_charge=item_making_charge,

                    customization_charge=Decimal(
                        "0"
                    ),

                    gst_rate=Decimal(
                        str(
                            product.gst_rate or 3
                        )
                    ),

                    gst_amount=item_gst
                )

                db.session.add(
                    order_item
                )

                # -------------------------------------------------
                # Update inventory
                # -------------------------------------------------

                change_stock(
                    product,
                    -quantity,
                    note=(
                        f"Order "
                        f"{order.order_number}"
                    )
                )

            # =================================================
            # CREATE PAYMENT
            # =================================================

            payment_id = (
                "PAY-"
                + uuid.uuid4().hex[:12].upper()
            )

            transaction_id = (
                "TXN-"
                + uuid.uuid4().hex[:10].upper()
            )

            payment_record = Payment(

                payment_id=payment_id,

                order_id=order.id,

                customer_id=customer.id,

                amount=total,

                payment_method=payment_method,

                transaction_id=transaction_id,

                payment_status=payment_status
            )

            db.session.add(
                payment_record
            )

            # =================================================
            # CREATE INVOICE
            # =================================================

            invoice_number = (
                "INV-"
                + datetime.now().strftime(
                    "%Y%m%d"
                )
                + "-"
                + uuid.uuid4().hex[:6].upper()
            )

            invoice = Invoice(

                invoice_number=invoice_number,

                order_id=order.id
            )

            db.session.add(
                invoice
            )

            # =================================================
            # CLEAR CART
            # =================================================

            for cart_item in list(
                cart.items
            ):

                db.session.delete(
                    cart_item
                )

            # =================================================
            # FINAL FLUSH
            # =================================================

            db.session.flush()

            # =================================================
            # COMMIT EVERYTHING
            # =================================================

            db.session.commit()

            # =================================================
            # SAVE LAST ORDER
            # =================================================

            session["last_order_id"] = (
                order.id
            )

            # =================================================
            # SUCCESS
            # =================================================

            return redirect(
                url_for(
                    "products.order_success",
                    order_id=order.id
                )
            )

        except Exception as error:

            # ------------------------------------------------
            # Rollback entire transaction
            # ------------------------------------------------

            db.session.rollback()

            # ------------------------------------------------
            # Print complete traceback
            # ------------------------------------------------

            print(
                "\n"
                + "=" * 70
            )

            print(
                "ORDER CREATION ERROR"
            )

            print(
                "=" * 70
            )

            print(
                repr(error)
            )

            traceback.print_exc()

            print(
                "=" * 70
                + "\n"
            )

            flash(
                "Unable to place your order. "
                "Please try again.",
                "danger"
            )

            return redirect(
                url_for(
                    "products.payment"
                )
            )

    # ========================================================
    # PAYMENT PAGE
    # ========================================================

    return render_template(
        "payment.html",

        customer=customer,

        items=items,

        subtotal=float(
            subtotal
        ),

        discount=float(
            discount
        ),

        making_charges=float(
            making_charges
        ),

        gst=float(
            gst
        ),

        total=float(
            total
        )
    )


# ============================================================
# ORDER SUCCESS
# ============================================================

@products_bp.route(
    "/order-success/<int:order_id>"
)
@login_required
def order_success(order_id):

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        flash(
            "Customer profile not found.",
            "danger"
        )

        return redirect(
            url_for("products.index")
        )

    order = Order.query.filter_by(
        id=order_id,
        customer_id=customer.id
    ).first_or_404()

    return render_template(
        "order-success.html",
        order=order
    )


# ============================================================
# USER PROFILE
# ============================================================

@products_bp.route(
    "/profile"
)
@login_required
def profile():

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        flash(
            "Customer profile not found.",
            "danger"
        )

        return redirect(
            url_for("products.index")
        )

    orders = (
        Order.query
        .filter_by(
            customer_id=customer.id
        )
        .order_by(
            Order.order_date.desc()
        )
        .all()
    )

    return render_template(
        "profile.html",
        customer=customer,
        orders=orders
    )


# ============================================================
# TRACK ORDER
# ============================================================

@products_bp.route(
    "/orders/<int:order_id>"
)
@login_required
def track_order(order_id):

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        flash(
            "Customer profile not found.",
            "danger"
        )

        return redirect(
            url_for("products.index")
        )

    order = Order.query.filter_by(
        id=order_id,
        customer_id=customer.id
    ).first_or_404()

    return render_template(
        "track-order.html",
        order=order
    )


# ============================================================
# WISHLIST
# ============================================================

@products_bp.route(
    "/wishlist"
)
@login_required
def wishlist():

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        return redirect(
            url_for("auth.login")
        )

    wishlist_items = (
        Wishlist.query
        .filter_by(
            customer_id=customer.id
        )
        .order_by(
            Wishlist.created_at.desc()
        )
        .all()
    )

    return render_template(
        "wishlist.html",
        wishlist_items=wishlist_items
    )


# ============================================================
# ADD TO WISHLIST
# ============================================================

@products_bp.route(
    "/wishlist/add/<int:product_id>",
    methods=["POST"]
)
@login_required
def add_to_wishlist(product_id):

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        return redirect(
            url_for("auth.login")
        )

    product = Product.query.get_or_404(
        product_id
    )

    # --------------------------------------------------------
    # Check existing wishlist item
    # --------------------------------------------------------

    existing = Wishlist.query.filter_by(
        customer_id=customer.id,
        product_id=product.id
    ).first()

    if existing:

        flash(
            "Product is already in your wishlist.",
            "info"
        )

        return redirect(
            request.referrer
            or url_for("products.index")
        )

    wishlist_item = Wishlist(
        customer_id=customer.id,
        product_id=product.id
    )

    db.session.add(
        wishlist_item
    )

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        traceback.print_exc()

        flash(
            "Unable to add product to wishlist.",
            "danger"
        )

        return redirect(
            request.referrer
            or url_for("products.index")
        )

    flash(
        f"{product.name} added to your wishlist.",
        "success"
    )

    return redirect(
        request.referrer
        or url_for("products.index")
    )


# ============================================================
# REMOVE FROM WISHLIST
# ============================================================

@products_bp.route(
    "/wishlist/remove/<int:product_id>",
    methods=["POST"]
)
@login_required
def remove_from_wishlist(product_id):

    customer = Customer.query.filter_by(
        user_id=current_user.id
    ).first()

    if not customer:

        return redirect(
            url_for("auth.login")
        )

    wishlist_item = Wishlist.query.filter_by(
        customer_id=customer.id,
        product_id=product_id
    ).first()

    if wishlist_item:

        db.session.delete(
            wishlist_item
        )

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            traceback.print_exc()

            flash(
                "Unable to remove product.",
                "danger"
            )

            return redirect(
                request.referrer
                or url_for("products.wishlist")
            )

        flash(
            "Product removed from your wishlist.",
            "success"
        )

    return redirect(
        request.referrer
        or url_for("products.wishlist")
    )
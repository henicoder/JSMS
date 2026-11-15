from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from ..models import User, Customer
from ..extensions import db, limiter


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


# =========================================
# LOGIN
# =========================================

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":

        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if (
            user
            and user.status == "active"
            and user.check_password(password)
        ):
            login_user(user)

            if user.role in ("admin", "employee"):
                return redirect(url_for("admin.dashboard"))

            return redirect(url_for("main.home"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


# =========================================
# REGISTER
# =========================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":

        # Get form data safely
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").lower().strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # ---------------------------------
        # Basic validation
        # ---------------------------------

        if not name:
            flash("Please enter your full name.", "danger")
            return render_template("auth/register.html")

        if not email:
            flash("Please enter your email address.", "danger")
            return render_template("auth/register.html")

        if not password:
            flash("Please enter a password.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "danger"
            )
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        # ---------------------------------
        # Check existing email
        # ---------------------------------

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered.", "warning")
            return render_template("auth/register.html")

        # ---------------------------------
        # Create User
        # ---------------------------------

        user = User(
            name=name,
            email=email,
            role="customer",
            phone=phone
        )

        user.set_password(password)

        db.session.add(user)

        # Get generated user ID
        db.session.flush()

        # ---------------------------------
        # Create Customer
        # ---------------------------------

        customer = Customer(
            user_id=user.id,
            name=name,
            email=email,
            phone=phone
        )

        db.session.add(customer)

        # ---------------------------------
        # Save to database
        # ---------------------------------

        db.session.commit()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# =========================================
# LOGOUT
# =========================================

@auth_bp.post("/logout")
def logout():

    logout_user()

    return redirect(url_for("main.home"))
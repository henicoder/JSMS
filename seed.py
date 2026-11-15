from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models import User, Customer, Category, Product, Inventory

app = create_app()

def seed_data():
    with app.app_context():
        db.create_all()

        # Seed Users
        users = [
            {
                "name": "Admin User",
                "email": "admin@jewellery.com",
                "password": "Admin@123",
                "role": "admin",
                "phone": "9876543210"
            },
            {
                "name": "Employee User",
                "email": "employee@jewellery.com",
                "password": "Employee@123",
                "role": "employee",
                "phone": "9876543211"
            },
            {
                "name": "Customer User",
                "email": "customer@example.com",
                "password": "Customer@123",
                "role": "customer",
                "phone": "9876543212"
            }
        ]

        for u_data in users:
            existing = User.query.filter_by(email=u_data["email"]).first()
            if not existing:
                user = User(
                    name=u_data["name"],
                    email=u_data["email"],
                    role=u_data["role"],
                    phone=u_data["phone"]
                )
                user.set_password(u_data["password"])
                db.session.add(user)
                db.session.flush()

                if user.role == "customer":
                    customer = Customer(
                        user_id=user.id,
                        name=user.name,
                        email=user.email,
                        phone=user.phone,
                        address="123 Luxury Avenue",
                        city="Mumbai",
                        state="Maharashtra",
                        pincode="400001"
                    )
                    db.session.add(customer)

        # Seed Categories
        categories_data = [
            {"name": "Chains", "description": "Elegant gold and silver chains"},
            {"name": "Bracelets", "description": "Designer bracelets for all occasions"},
            {"name": "Pendants", "description": "Sparkling pendants and lockets"}
        ]

        cat_objs = {}
        for c in categories_data:
            cat = Category.query.filter_by(name=c["name"]).first()
            if not cat:
                cat = Category(name=c["name"], description=c["description"])
                db.session.add(cat)
                db.session.flush()
            cat_objs[c["name"]] = cat

        # Seed Sample Products
        products_data = [
            {
                "sku": "CHN-001",
                "name": "Classic Gold Chain",
                "description": "22K finely crafted traditional chain",
                "price": Decimal("45000.00"),
                "metal_type": "Gold",
                "purity": "22K",
                "weight": Decimal("10.500"),
                "making_charge": Decimal("3500.00"),
                "making_charge_percent": Decimal("8.00"),
                "gst_rate": Decimal("3.00"),
                "stock_quantity": 10,
                "image": "chain1.jpeg",
                "category": cat_objs.get("Chains")
            },
            {
                "sku": "BRC-001",
                "name": "Luxury Diamond Bracelet",
                "description": "18K white gold diamond studded bracelet",
                "price": Decimal("65000.00"),
                "metal_type": "Gold",
                "purity": "18K",
                "weight": Decimal("15.200"),
                "making_charge": Decimal("5000.00"),
                "making_charge_percent": Decimal("10.00"),
                "gst_rate": Decimal("3.00"),
                "stock_quantity": 5,
                "image": "bracelet1.jpeg",
                "category": cat_objs.get("Bracelets")
            },
            {
                "sku": "PND-001",
                "name": "Royal Emerald Pendant",
                "description": "Exquisite handcrafted pendant with natural emerald",
                "price": Decimal("28000.00"),
                "metal_type": "Gold",
                "purity": "22K",
                "weight": Decimal("6.800"),
                "making_charge": Decimal("2000.00"),
                "making_charge_percent": Decimal("7.00"),
                "gst_rate": Decimal("3.00"),
                "stock_quantity": 8,
                "image": "pendant.jpg",
                "category": cat_objs.get("Pendants")
            }
        ]

        for p_data in products_data:
            if not Product.query.filter_by(sku=p_data["sku"]).first():
                prod = Product(
                    sku=p_data["sku"],
                    name=p_data["name"],
                    description=p_data["description"],
                    price=p_data["price"],
                    metal_type=p_data["metal_type"],
                    purity=p_data["purity"],
                    weight=p_data["weight"],
                    making_charge=p_data["making_charge"],
                    making_charge_percent=p_data["making_charge_percent"],
                    gst_rate=p_data["gst_rate"],
                    stock_quantity=p_data["stock_quantity"],
                    image=p_data["image"],
                    category_id=p_data["category"].id if p_data["category"] else 1
                )
                db.session.add(prod)
                db.session.flush()

                inventory = Inventory(
                    product_id=prod.id,
                    quantity=prod.stock_quantity
                )
                db.session.add(inventory)

        db.session.commit()
        print("Database seeded successfully with demo users and products!")

if __name__ == "__main__":
    seed_data()

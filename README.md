# Jewellery Shop Management System (JSMS)

A college/viva-ready full-stack jewellery shop management system using Python, Flask, SQLAlchemy, MySQL, HTML, CSS, JavaScript, Bootstrap 5 and Chart.js.

## Features
- Customer registration/login
- Admin and employee roles
- Product/category CRUD
- Search/filter/sort
- Cart and checkout
- GST and making-charge calculation
- Demo payment flow
- Orders and order-status timeline
- Inventory and low-stock alerts
- Customer, employee and supplier management
- Invoice generation with ReportLab
- Sales/inventory/customer/product/payment reports
- Audit logging
- Validation, error handling and logging
- Responsive luxury UI
- Seed/demo data
- Pytest smoke tests

## Setup
1. Create MySQL database:
   `CREATE DATABASE jewellery_shop_db;`
2. Create and activate a virtual environment:
   `python -m venv venv`
   Windows: `venv\Scripts\activate`
3. Install packages:
   `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set the MySQL password.
5. Seed demo data:
   `python seed.py`
6. Run:
   `python run.py`
7. Open: http://127.0.0.1:5000

## Demo credentials
- Admin: admin@jewellery.com / Admin@123
- Employee: employee@jewellery.com / Employee@123
- Customer: customer@example.com / Customer@123

Development-only credentials. Change them for real deployment.

## Practical 8
The project follows snake_case for Python, PascalCase for classes, UPPER_CASE for constants and camelCase for JavaScript. It uses docstrings, logging, validation, role checks, reusable services, and tests.

## API examples
GET /api/products
GET /api/products/<id>
POST /api/products
GET /api/reports/sales

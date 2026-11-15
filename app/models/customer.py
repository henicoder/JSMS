from datetime import datetime
from ..extensions import db

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False, index=True)
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    city = db.Column(db.String(80))
    state = db.Column(db.String(80))
    pincode = db.Column(db.String(20))
    status = db.Column(db.String(20), default="active")
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("customer_profile", uselist=False))

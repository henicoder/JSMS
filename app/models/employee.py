from datetime import datetime
from ..extensions import db

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(30))
    department = db.Column(db.String(80))
    joining_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="active")
    user = db.relationship("User", backref=db.backref("employee_profile", uselist=False))

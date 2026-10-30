import uuid

def create_demo_payment(amount, method="Demo Payment"):
    return {
        "payment_id": "PAY-" + uuid.uuid4().hex[:10].upper(),
        "transaction_id": "DEMO-" + uuid.uuid4().hex[:12].upper(),
        "amount": amount,
        "method": method,
        "status": "Successful"
    }

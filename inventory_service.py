from ..extensions import db
from ..models import Inventory, InventoryTransaction


def sync_inventory(product):
    inventory = Inventory.query.filter_by(product_id=product.id).first()

    if not inventory:
        inventory = Inventory(
            product_id=product.id,
            quantity=product.stock_quantity
        )
        db.session.add(inventory)
    else:
        inventory.quantity = product.stock_quantity

    return inventory


def change_stock(product, delta, note=""):
    new_quantity = product.stock_quantity + delta

    if new_quantity < 0:
        raise ValueError("Insufficient stock.")

    product.stock_quantity = new_quantity

    sync_inventory(product)

    db.session.add(
        InventoryTransaction(
            product_id=product.id,
            transaction_type="IN" if delta > 0 else "OUT",
            quantity=abs(delta),
            note=note
        )
    )
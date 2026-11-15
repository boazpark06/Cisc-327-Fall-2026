from notification_service import (
    send_notification,
    SUBJECT_PREFIX,
    DEFAULT_RECIPIENT,
)

from flask import Blueprint, jsonify, request

from app import store
from app.models.transaction import Transaction

transactions_bp = Blueprint("transactions", __name__, url_prefix="/transactions")


@transactions_bp.route("", methods=["GET"])
def list_transactions():
    results = list(store.transactions.values())
    product_id = request.args.get("product_id", type=int)
    supplier_id = request.args.get("supplier_id", type=int)
    if product_id is not None:
        results = [t for t in results if t.product_id == product_id]
    if supplier_id is not None:
        results = [t for t in results if t.supplier_id == supplier_id]
    return jsonify([t.to_dict() for t in results])


@transactions_bp.route("", methods=["POST"])
def create_transaction():
    data = request.get_json()
    product = store.products.get(data["product_id"])
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    quantity = data["quantity"]
    tx_type = data["type"]
    previous_quantity = product.quantity_on_hand

    if tx_type == "IN":
        product.quantity_on_hand += quantity
    elif tx_type == "OUT":
        product.quantity_on_hand -= quantity
    else:
        return jsonify({"error": "type must be IN or OUT"}), 400

    transaction_id = store.next_id("transaction")
    transaction = Transaction(
        id=transaction_id,
        product_id=data["product_id"],
        supplier_id=data.get("supplier_id"),
        type=tx_type,
        quantity=quantity,
    )
    #store.transactions[transaction_id] = transaction
    #return jsonify(transaction.to_dict()), 201
    store.transactions[transaction_id] = transaction

    response_data = transaction.to_dict()

    # Send an alert when an outgoing transaction causes low stock
    if (
        tx_type == "OUT"
        and previous_quantity > product.reorder_level
        and product.quantity_on_hand <= product.reorder_level
    ):
        recipient = DEFAULT_RECIPIENT
        subject = f"{SUBJECT_PREFIX} Low stock alert"
        message = (
            f"{product.name} (SKU: {product.sku}) is low on stock: "
            f"{product.quantity_on_hand} units remaining "
            f"(reorder level: {product.reorder_level})."
        )

        response_data["notification_sent"] = send_notification(
            recipient, subject, message
        )

    return jsonify(response_data), 201

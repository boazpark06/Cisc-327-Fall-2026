
def test_list_suppliers(client):
    # Initially there should be no suppliers
    response = client.get("/suppliers")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_supplier(client):
    # Create a supplier using the API
    response = client.post("/suppliers", json={
        "name": "ABC Supplies",
        "contact_email": "abc@example.com"
    })

    assert response.status_code == 201

    # Verify the returned supplier information
    supplier = response.get_json()
    assert supplier["name"] == "ABC Supplies"
    assert supplier["contact_email"] == "abc@example.com"


def test_get_supplier(client):
    # Create a supplier first
    created = client.post("/suppliers", json={
        "name": "ABC Supplies",
        "contact_email": "abc@example.com"
    })

    supplier_id = created.get_json()["id"]

    # Retrieve the supplier using its ID
    response = client.get(f"/suppliers/{supplier_id}")

    assert response.status_code == 200
    assert response.get_json()["name"] == "ABC Supplies"


def test_update_supplier(client):
    # Create a supplier
    created = client.post("/suppliers", json={
        "name": "Old Name",
        "contact_email": "old@example.com"
    })

    supplier_id = created.get_json()["id"]

    # Update the supplier
    response = client.put(f"/suppliers/{supplier_id}", json={
        "name": "New Name"
    })

    assert response.status_code == 200

    # Verify the updated name was saved
    updated = client.get(f"/suppliers/{supplier_id}")
    assert updated.get_json()["name"] == "New Name"
    assert updated.get_json()["contact_email"] == "old@example.com"


def test_delete_supplier(client):
    # Create a supplier
    created = client.post("/suppliers", json={
        "name": "ABC Supplies",
        "contact_email": "abc@example.com"
    })

    supplier_id = created.get_json()["id"]

    # Delete the supplier
    response = client.delete(f"/suppliers/{supplier_id}")
    assert response.status_code == 204

    # Verify it no longer exists
    response = client.get(f"/suppliers/{supplier_id}")
    assert response.status_code == 404


def test_list_supplier_products(client):
    # Create a supplier
    supplier = client.post("/suppliers", json={
        "name": "ABC Supplies",
        "contact_email": "abc@example.com"
    }).get_json()

    # Create a product
    product = client.post("/products", json={
        "name": "Hammer",
        "sku": "HAM-001",
        "quantity_on_hand": 10
    }).get_json()

    # Record incoming stock from the supplier
    transaction = client.post("/transactions", json={
        "product_id": product["id"],
        "supplier_id": supplier["id"],
        "type": "IN",
        "quantity": 5
    })

    assert transaction.status_code == 201

    # Check that the supplier is associated with this product
    response = client.get(f"/suppliers/{supplier['id']}/products")

    assert response.status_code == 200
    products = response.get_json()
    assert len(products) == 1
    assert products[0]["name"] == "Hammer"


def test_list_purchase_orders(client):
    # Initially there should be no purchase orders
    response = client.get("/purchase-orders")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_purchase_order(client):
    # Create a supplier
    supplier = client.post("/suppliers", json={
        "name": "ABC Supplies",
        "contact_email": "abc@example.com"
    }).get_json()

    # Create a product
    product = client.post("/products", json={
        "name": "Hammer",
        "sku": "HAM-001",
        "quantity_on_hand": 10
    }).get_json()

    # Create a purchase order for 20 units
    response = client.post("/purchase-orders", json={
        "supplier_id": supplier["id"],
        "product_id": product["id"],
        "quantity_ordered": 20
    })

    assert response.status_code == 201

    order = response.get_json()
    assert order["supplier_id"] == supplier["id"]
    assert order["product_id"] == product["id"]
    assert order["quantity_ordered"] == 20
    assert order["status"] == "pending"

    # Verify that the order was saved
    orders = client.get("/purchase-orders").get_json()
    assert len(orders) == 1
    assert orders[0]["id"] == order["id"]


def test_get_purchase_order(client):
    # Create a supplier
    supplier = client.post("/suppliers", json={
        "name": "ABC Supplies",
        "contact_email": "abc@example.com"
    }).get_json()

    # Create a product
    product = client.post("/products", json={
        "name": "Hammer",
        "sku": "HAM-001",
        "quantity_on_hand": 10
    }).get_json()

    # Create a purchase order
    order = client.post("/purchase-orders", json={
        "supplier_id": supplier["id"],
        "product_id": product["id"],
        "quantity_ordered": 20
    }).get_json()

    # Retrieve the purchase order
    response = client.get(f"/purchase-orders/{order['id']}")

    assert response.status_code == 200
    assert response.get_json()["id"] == order["id"]
    assert response.get_json()["quantity_ordered"] == 20
    assert response.get_json()["status"] == "pending"


# Helper function to create a supplier, product, and purchase order
def setup_purchase_order(client):
    supplier = client.post("/suppliers", json={
        "name": "ABC Supplies",
        "contact_email": "abc@example.com"
    }).get_json()

    product = client.post("/products", json={
        "name": "Hammer",
        "sku": "HAM-001",
        "quantity_on_hand": 10
    }).get_json()

    order = client.post("/purchase-orders", json={
        "supplier_id": supplier["id"],
        "product_id": product["id"],
        "quantity_ordered": 20
    }).get_json()

    return product["id"], order["id"]


def test_receive_purchase_order(client):
    product_id, order_id = setup_purchase_order(client)

    # Receive the purchase order
    response = client.put(f"/purchase-orders/{order_id}/receive")

    assert response.status_code == 200
    assert response.get_json()["status"] == "received"
    assert response.get_json()["received_date"] is not None

    # Verify an incoming transaction was recorded
    transactions = client.get("/transactions").get_json()

    assert len(transactions) == 1
    assert transactions[0]["product_id"] == product_id
    assert transactions[0]["type"] == "IN"
    assert transactions[0]["quantity"] == 20


def test_receive_nonexistent_purchase_order(client):
    # Attempt to receive an order that does not exist
    response = client.put("/purchase-orders/999/receive")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Purchase order not found"


def test_receive_purchase_order_twice(client):
    product_id, order_id = setup_purchase_order(client)

    # First receipt should succeed
    first = client.put(f"/purchase-orders/{order_id}/receive")
    assert first.status_code == 200

    # Second receipt should be rejected
    second = client.put(f"/purchase-orders/{order_id}/receive")
    assert second.status_code == 400

    # The transaction should only be recorded once
    transactions = client.get("/transactions").get_json()
    assert len(transactions) == 1


def test_receiving_purchase_order_updates_stock(client):
    product_id, order_id = setup_purchase_order(client)

    # Initial stock is 10
    before = client.get(f"/products/{product_id}/stock-level")
    assert before.get_json()["quantity_on_hand"] == 10

    # Receive 20 additional units
    response = client.put(f"/purchase-orders/{order_id}/receive")
    assert response.status_code == 200

    # Expected stock: 10 + 20 = 30
    after = client.get(f"/products/{product_id}/stock-level")

    assert after.get_json()["quantity_on_hand"] == 30


def test_receiving_order_increases_stock_only_once(client):
    product_id, order_id = setup_purchase_order(client)

    # Receive 20 units, increasing stock from 10 to 30
    first = client.put(f"/purchase-orders/{order_id}/receive")
    assert first.status_code == 200

    # Receiving the same order again should fail
    second = client.put(f"/purchase-orders/{order_id}/receive")
    assert second.status_code == 400

    # Stock must remain at 30
    stock = client.get(f"/products/{product_id}/stock-level")
    assert stock.get_json()["quantity_on_hand"] == 30

    # Only one incoming transaction should exist
    transactions = client.get("/transactions").get_json()
    assert len(transactions) == 1


def test_receiving_multiple_orders_accumulates_stock(client):
    product_id, first_order_id = setup_purchase_order(client)

    # Retrieve the supplier from the first order
    first_order = client.get(
        f"/purchase-orders/{first_order_id}"
    ).get_json()

    # Create a second purchase order for 5 units
    second_response = client.post("/purchase-orders", json={
        "supplier_id": first_order["supplier_id"],
        "product_id": product_id,
        "quantity_ordered": 5
    })

    assert second_response.status_code == 201
    second_order_id = second_response.get_json()["id"]

    # Receive both purchase orders
    first = client.put(f"/purchase-orders/{first_order_id}/receive")
    second = client.put(f"/purchase-orders/{second_order_id}/receive")

    assert first.status_code == 200
    assert second.status_code == 200

    # Initial stock 10 + 20 + 5 = 35
    stock = client.get(f"/products/{product_id}/stock-level")
    assert stock.get_json()["quantity_on_hand"] == 35

    # Verify both incoming transactions
    transactions = client.get("/transactions").get_json()
    assert len(transactions) == 2
    assert sum(t["quantity"] for t in transactions) == 25




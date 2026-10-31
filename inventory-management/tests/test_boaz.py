
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


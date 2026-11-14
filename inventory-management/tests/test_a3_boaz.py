from unittest.mock import patch

def test_low_stock_notification_success_stub(client, monkeypatch):
    # Stub the notification service to always return True
    monkeypatch.setattr(
        "app.routes.transactions.send_notification",
        lambda recipient, subject, message: True
    )

    # Create a product with 15 units and a reorder level of 10
    response = client.post("/products", json={
        "name": "Bolts",
        "sku": "BOLT-001",
        "quantity_on_hand": 15,
        "reorder_level": 10
    })

    product_id = response.get_json()["id"]

    # Remove 6 units, reducing stock from 15 to 9
    response = client.post("/transactions", json={
        "product_id": product_id,
        "type": "OUT",
        "quantity": 6
    })

    # Verify the transaction succeeded
    assert response.status_code == 201

    # Verify the notification was reported as successful
    assert response.get_json()["notification_sent"] is True

    # Verify the inventory was actually updated
    stock_response = client.get(f"/products/{product_id}/stock-level")
    assert stock_response.status_code == 200
    assert stock_response.get_json()["quantity_on_hand"] == 9


def test_low_stock_notification_mock(client):
    # Create a product with 15 units and reorder level of 10
    response = client.post("/products", json={
        "name": "Bolts",
        "sku": "BOLT-001",
        "quantity_on_hand": 15,
        "reorder_level": 10
    })

    product_id = response.get_json()["id"]

    # Mock the notification service
    with patch(
        "app.routes.transactions.send_notification",
        return_value=True
    ) as mock_send:

        # Reduce stock from 15 to 9
        response = client.post("/transactions", json={
            "product_id": product_id,
            "type": "OUT",
            "quantity": 6
        })

        # Verify application behavior
        assert response.status_code == 201
        assert response.get_json()["notification_sent"] is True

        # Verify the notification was called exactly once
        # with the correct arguments
        mock_send.assert_called_once_with(
            "inventory-staff",
            "[Harborview Hardware] Low stock alert",
            "Bolts (SKU: BOLT-001) is low on stock: "
            "9 units remaining (reorder level: 10)."
        )

    # Verify inventory was updated
    stock_response = client.get(f"/products/{product_id}/stock-level")
    assert stock_response.status_code == 200
    assert stock_response.get_json()["quantity_on_hand"] == 9


def test_low_stock_products(client):
    # Create a product at the reorder level
    low_product = client.post("/products", json={
        "name": "Bolts",
        "sku": "BOLT-001",
        "quantity_on_hand": 5,
        "reorder_level": 5
    }).get_json()

    # Create a product with sufficient stock
    high_product = client.post("/products", json={
        "name": "Screws",
        "sku": "SCREW-001",
        "quantity_on_hand": 20,
        "reorder_level": 5
    }).get_json()

    # Request products that are low on stock
    response = client.get("/products/low-stock")

    assert response.status_code == 200

    products = response.get_json()
    product_ids = [p["id"] for p in products]

    # Only the low-stock product should appear
    assert low_product["id"] in product_ids
    assert high_product["id"] not in product_ids
    assert len(products) == 1


def test_nonexistent_product_operations(client):
    # Attempt to retrieve a nonexistent product
    response = client.get("/products/999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Product not found"

    # Attempt to update a nonexistent product
    response = client.put("/products/999", json={
        "name": "Updated Product"
    })
    assert response.status_code == 404
    assert response.get_json()["error"] == "Product not found"

    # Attempt to delete a nonexistent product
    response = client.delete("/products/999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Product not found"


def test_create_purchase_order_invalid_supplier(client):
    # Try to create an order with a nonexistent supplier
    response = client.post("/purchase-orders", json={
        "supplier_id": 999,
        "product_id": 1,
        "quantity_ordered": 10
    })

    assert response.status_code == 404
    assert response.get_json()["error"] == "Supplier not found"

    # No purchase order should have been created
    assert client.get("/purchase-orders").get_json() == []


def test_create_purchase_order_invalid_product(client):
    # Create a valid supplier
    supplier_response = client.post("/suppliers", json={
        "name": "Hardware Supplier",
        "contact_email": "supplier@example.com"
    })

    assert supplier_response.status_code == 201
    supplier_id = supplier_response.get_json()["id"]

    # Try to order a nonexistent product
    response = client.post("/purchase-orders", json={
        "supplier_id": supplier_id,
        "product_id": 999,
        "quantity_ordered": 10
    })

    assert response.status_code == 404
    assert response.get_json()["error"] == "Product not found"

    # No purchase order should have been created
    assert client.get("/purchase-orders").get_json() == []


def test_get_nonexistent_purchase_order_a3(client):
    # Try to retrieve an order that doesn't exist
    response = client.get("/purchase-orders/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Purchase order not found"

    # The purchase-order collection remains empty
    assert client.get("/purchase-orders").get_json() == []


def test_nonexistent_product_stock_level(client):
    # Request stock information for a product that doesn't exist
    response = client.get("/products/999/stock-level")

    # Verify the application handles the missing product
    assert response.status_code == 404
    assert response.get_json()["error"] == "Product not found"





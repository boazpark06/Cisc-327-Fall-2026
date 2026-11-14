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


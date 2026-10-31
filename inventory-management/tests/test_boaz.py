
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

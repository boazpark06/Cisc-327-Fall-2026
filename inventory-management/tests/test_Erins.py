from datetime import date

def add_prod(client, *, name="NULL", sku="NULL",stock=10):
    response = client.post(
        "/products",
        json={
            "name": name,
            "sku": sku,
            "unit_price": 2.50,
            "quantity_on_hand": stock, 
	     },
    )
    assert response.status_code == 201
    return response.get_json()

# product list test

def test_list_products(client):
    p1 = add_prod(client, name="testvar1", sku="1", stock=10)
    p2 = add_prod(client, name="testvar2", sku="2", stock=20)

    response = client.get("/products")

    assert response.status_code == 200

    products = response.get_json()

    assert len(products) == 2
    assert {p["id"] for p in products} == {p1["id"], p2["id"]}
    assert {p["name"] for p in products} == {"testvar1", "testvar2"}


# product creation test

def test_create_product(client):
    response = client.post("/products", json={
        "name": "testvar3",
        "sku": "3",
        "unit_price": 2.50,
        "quantity_on_hand": 15
    })

    assert response.status_code == 201

    product = response.get_json()

    assert product["name"] == "testvar3"
    assert product["sku"] == "3"
    assert product["unit_price"] == 2.50
    assert product["quantity_on_hand"] == 15

    check = client.get(f"/products/{product['id']}")

# single product list test

def test_get_product(client):
    p1 = add_prod(client, name="testvar4", sku="4", stock=15)

    response = client.get(f"/products/{p1['id']}")

    assert response.status_code == 200

    product = response.get_json()

    assert product["id"] == p1["id"]
    assert product["name"] == "testvar4"
    assert product["sku"] == "4"
    assert product["quantity_on_hand"] == 15
    assert product["unit_price"] == 2.50

#product update test

def test_update_product(client):
    p1 = add_prod(client, name="testvar5", sku="5", stock=10)

    response = client.put(f"/products/{p1['id']}", json={
        "name": "updatedvar5",
        "quantity_on_hand": 25
    })

    assert response.status_code == 200

    check = client.get(f"/products/{p1['id']}")

    assert check.status_code == 200

    product = check.get_json()

    assert product["name"] == "updatedvar5"
    assert product["quantity_on_hand"] == 25
    assert product["id"] == p1["id"]
    assert product["sku"] == "5"
    assert product["unit_price"] == 2.50

# product delete test

def test_delete_product(client):
    p1 = add_prod(client, name="testvar6", sku="6", stock=10)

    response = client.delete(f"/products/{p1['id']}")

    assert response.status_code == 204

    check = client.get(f"/products/{p1['id']}")

    assert check.status_code == 404

    products = client.get("/products").get_json()

    assert all(p["id"] != p1["id"] for p in products)

# level test

def test_stock_level(client):
    p1 = add_prod(client, name="testvar7", sku="7", stock=25)

    response = client.get(f"/products/{p1['id']}/stock-level")

    assert response.status_code == 200

    stock = response.get_json()

    assert stock["product_id"] == p1["id"]
    assert stock["quantity_on_hand"] == 25

    client.put(f"/products/{p1['id']}", json={
        "quantity_on_hand": 10
    })

    updated = client.get(f"/products/{p1['id']}/stock-level")

    assert updated.status_code == 200
    assert updated.get_json()["quantity_on_hand"] == 10

# stock in test

def test_incoming_stock(client):
    p1 = add_prod(client, name="testvar8", sku="8", stock=10)

    response = client.post("/transactions", json={
        "product_id": p1["id"],
        "type": "IN",
        "quantity": 5
    })

    assert response.status_code == 201

    transaction = response.get_json()

    assert transaction["product_id"] == p1["id"]
    assert transaction["type"] == "IN"
    assert transaction["quantity"] == 5

    check = client.get(f"/products/{p1['id']}")

    assert check.status_code == 200
    assert check.get_json()["quantity_on_hand"] == 15

# stock out test

def test_outgoing_stock(client):
    p1 = add_prod(client, name="testvar9", sku="9", stock=15)

    response = client.post("/transactions", json={
        "product_id": p1["id"],
        "type": "OUT",
        "quantity": 5
    })

    assert response.status_code == 201

    transaction = response.get_json()

    assert transaction["product_id"] == p1["id"]
    assert transaction["type"] == "OUT"
    assert transaction["quantity"] == 5

    check = client.get(f"/products/{p1['id']}")

    assert check.status_code == 200
    assert check.get_json()["quantity_on_hand"] == 10

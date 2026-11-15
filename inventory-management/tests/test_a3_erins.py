
from app import store
# UI create test
def test_ui_create_product(client):
    response = client.post("/ui/products", data={
        "name": "test1",
        "sku": "1",
        "unit_price": "1.00",
        "quantity_on_hand": "1"
    })

    assert response.status_code == 302

    products = [p for p in store.products.values() if p.sku == "1"]

    assert len(products) == 1
    assert products[0].name == "test1"
    assert products[0].unit_price == 1.00
    assert products[0].quantity_on_hand == 1

# UI delete test
def test_ui_delete_product(client):
    response = client.post("/ui/products", data={
        "name": "test2",
        "sku": "2",
        "unit_price": "2.00",
        "quantity_on_hand": "2"
    })

    assert response.status_code == 302

    product = next(p for p in store.products.values()
                   if p.sku == "2")

    response = client.post(f"/ui/products/{product.id}/delete")

    assert response.status_code == 302
    assert product.id not in store.products

# UI incoming test
def test_ui_incoming(client):
    client.post("/ui/products", data={
        "name": "test3",
        "sku": "3",
        "unit_price": "3",
        "quantity_on_hand": "3"
    })

    product = next(p for p in store.products.values()
                   if p.sku == "3")

    response = client.post("/ui/transactions", data={
        "product_id": str(product.id),
        "type": "IN",
        "quantity": "3"
    })

    assert response.status_code == 302
    assert product.quantity_on_hand == 6

    transactions = [t for t in store.transactions.values()
                    if t.product_id == product.id]

    assert len(transactions) == 1
    assert transactions[0].type == "IN"
    assert transactions[0].quantity == 3

# UI outgoing test
def test_ui_outgoing(client):
    client.post("/ui/products", data={
        "name": "test4",
        "sku": "4",
        "unit_price": "4",
        "quantity_on_hand": "4"
    })

    product = next(p for p in store.products.values()
                   if p.sku == "4")

    response = client.post("/ui/transactions", data={
        "product_id": str(product.id),
        "type": "OUT",
        "quantity": "4"
    })

    assert response.status_code == 302
    assert product.quantity_on_hand == 0

    transactions = [t for t in store.transactions.values()
                    if t.product_id == product.id]

    assert len(transactions) == 1
    assert transactions[0].type == "OUT"
    assert transactions[0].quantity == 4

# centigrade

Install requirements using the command:

```
pip3 install -r requirements.txt
```


Run the app using the command:

```
uvicorn main:app --reload
```

# Create customer
```
curl -X POST http://localhost:8000/customers \
  -H "Content-Type: application/json" \
  -d '{
        "first_name": "John",
        "last_name": "Doe",
        "email_address": "john.doe@example.com",
        "phone_number": "123-456-7890",
        "physical_address": "123 Main St"
      }'
```

# Get customer

```
curl http://localhost:8000/customers/<customer_id>
```

# Create product
```
curl -X POST http://localhost:8000/product \
  -H "Content-Type: application/json" \
  -d '{
        "product_name": "Laptop",
        "description": "High-end gaming laptop",
        "price": 1999.99,
        "category": "Electronics"
      }'
```

# Create an order
```
curl -X POST http://localhost:8000/order \
  -H "Content-Type: application/json" \
  -d '{
        "customer_id": "<customer_id>",
        "product_ids": ["<product_id1>", "<product_id2>"]
      }'
```

# Add products to an order

```
curl -X POST http://localhost:8000/order/<order_id>/add-products \
  -H "Content-Type: application/json" \
  -d '{
        "product_ids": ["<product_id3>", "<product_id4>"]
      }'
```


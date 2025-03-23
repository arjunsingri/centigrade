from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
from uuid import uuid5
import uuid

app = FastAPI()

# In-memory data storage
customers_db = {}
products_db = {}
orders_db = {}

# Pydantic models
class Customer(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email_address: EmailStr
    phone_number: str
    physical_address: str
    creation_date: datetime

class Product(BaseModel):
    product_id: str
    product_name: str
    description: str
    price: float
    category: str

class Order(BaseModel):
    order_id: str
    customer_id: str
    order_date: datetime
    total_price: float
    status: str
    products: List[str] = []

class Product(BaseModel):
    product_id: str
    product_name: str
    description: str
    price: float
    category: str

class ProductCreateRequest(BaseModel):
    product_name: str
    description: str
    price: float
    category: str

class CreateOrderRequest(BaseModel):
    customer_id: str
    product_ids: List[str]

class AddProductsRequest(BaseModel):
    product_ids: List[str]

class CustomerCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email_address: EmailStr
    phone_number: str
    physical_address: str

# Allow creating customer entity
@app.post("/customers", response_model=Customer)
def create_customer(request: CustomerCreateRequest):
    # Generate deterministic UUID from email
    customer_id = str(uuid5(uuid.NAMESPACE_DNS, request.email_address))

    if customer_id in customers_db:
        raise HTTPException(status_code=409, detail=f"Customer already exists with this email {request.email_address}")

    customer = Customer(
        customer_id=customer_id,
        first_name=request.first_name,
        last_name=request.last_name,
        email_address=request.email_address,
        phone_number=request.phone_number,
        physical_address=request.physical_address,
        creation_date=datetime.utcnow()
    )

    customers_db[customer_id] = customer

    return customer

# Allow creating products
@app.post("/product", response_model=Product)
def create_product(product_request: ProductCreateRequest):

    combined = f"{product_request.product_name}:{product_request.category}"
    product_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, combined))

    if product_id in products_db.keys():
        raise HTTPException(status_code=409, detail=f"Duplicate product exists {product_request.product_name}:{product_request.category}")

    product = Product(
        product_id=product_id,
        product_name=product_request.product_name,
        description=product_request.description,
        price=product_request.price,
        category=product_request.category
    )
    products_db[product_id] = product
    return product

# 1. Query customer information
@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: str):
    customer = customers_db.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

def validate_products(product_ids: List[str]) -> float:
    total_price = 0.0

    # even if one product is not found, we fail the entire request
    for pid in product_ids:
        if pid not in products_db.keys():
            raise HTTPException(status_code=404, detail="Product with product-id {pid} not found")

        total_price += products_db[pid].price

    return total_price

# 2. Create an order
@app.post("/order", response_model=Order)
def create_order(request: CreateOrderRequest):
    if request.customer_id not in customers_db:
        raise HTTPException(status_code=404, detail="Customer not found")

    total_price = validate_products(request.product_ids) 

    order_id = str(uuid4())
    order = Order(
        order_id=order_id,
        customer_id=request.customer_id,
        order_date=datetime.utcnow(),
        total_price=total_price,
        status="Pending",
        products=request.product_ids
    )
    orders_db[order_id] = order
    return order


# 3. Add products to an order
@app.post("/order/{order_id}/add-products", response_model=Order)
def add_product_to_order(order_id: str, request: AddProductsRequest):
    order = orders_db.get(order_id)

    if not order:
        raise HTTPException(status_code=404, detail=f"Order with order-id {order_id} not found")

    pids = list(set(request.product_ids).union(set(order.products)))
    print(pids)
    total_price = validate_products(pids) 
    order.products = pids 
    order.total_price = total_price 

    return order


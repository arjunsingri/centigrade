from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
from uuid import uuid5
import uuid
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Table, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import enum

Base = declarative_base()
DATABASE_URL = "sqlite:///./store.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

app = FastAPI()

# Association Table for many-to-many between Orders and Products
order_product_association = Table(
    'order_product',
    Base.metadata,
    Column('order_id', ForeignKey('orders.order_id'), primary_key=True),
    Column('product_id', ForeignKey('products.product_id'), primary_key=True)
)

class OrderStatusEnum(str, enum.Enum):
    pending = "Pending"
    shipped = "Shipped"
    delivered = "Delivered"
    cancelled = "Cancelled"

class Customer(Base):
    __tablename__ = 'customers'

    customer_id = Column(String, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email_address = Column(String, unique=True, index=True)
    phone_number = Column(String)
    physical_address = Column(String)
    creation_date = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="customer")

class Product(Base):
    __tablename__ = 'products'

    product_id = Column(String, primary_key=True, index=True)
    product_name = Column(String)
    description = Column(String)
    price = Column(Float)
    category = Column(String)

    orders = relationship("Order", secondary=order_product_association, back_populates="products")

class Order(Base):
    __tablename__ = 'orders'

    order_id = Column(String, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    order_date = Column(DateTime, default=datetime.utcnow)
    total_price = Column(Float)
    status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.pending)

    customer = relationship("Customer", back_populates="orders")
    products = relationship("Product", secondary=order_product_association, back_populates="orders")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class CustomerResponse(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email_address: EmailStr
    phone_number: str
    physical_address: str
    creation_date: datetime
    
    class Config:
        orm_mode = True

class ProductResponse(BaseModel):
    product_id: str
    product_name: str
    description: str
    price: float
    category: str

    class Config:
        orm_mode = True

class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    order_date: datetime
    total_price: float
    status: str
    products: List[str] = []

    class Config:
        orm_mode = True

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

# Create tables
Base.metadata.create_all(bind=engine)

# Allow creating customer entity
@app.post("/customers", response_model=CustomerResponse)
def create_customer(request: CustomerCreateRequest, db: Session = Depends(get_db)):
    # Generate deterministic UUID from email
    customer_id = str(uuid5(uuid.NAMESPACE_DNS, request.email_address))
    
    existing = db.query(Customer).filter_by(customer_id=customer_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Customer ID {customer_id} already exists")

    db_customer = Customer(customer_id=customer_id, **request.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

# Allow creating products
@app.post("/product", response_model=ProductResponse)
def create_product(product_request: ProductCreateRequest, db: Session = Depends(get_db)):
    combined = f"{product_request.product_name}:{product_request.category}"
    product_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, combined))

    existing = db.query(Product).filter_by(product_id=product_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Product ID {product_id} already exists")

    db_product = Product(product_id=product_id, **product_request.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# 1. Query customer information
@app.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    existing = db.query(Customer).filter_by(customer_id=customer_id).first()
   
    if not existing:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    return existing 

def validate_products(product_ids: List[str]) -> float:
    total_price = 0.0

    # even if one product is not found, we fail the entire request
    for pid in product_ids:
        if pid not in products_db.keys():
            raise HTTPException(status_code=404, detail="Product with product-id {pid} not found")

        total_price += products_db[pid].price

    return total_price

# 2. Create an order
@app.post("/order", response_model=OrderResponse)
def create_order(request: CreateOrderRequest, db: Session = Depends(get_db)):
    existing = db.query(Customer).filter_by(customer_id=request.customer_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Customer {request.customer_id} not found")

    order_products = db.query(Product).filter(Product.product_id.in_(request.product_ids)).all()
    if len(order_products) != len(request.product_ids):
        raise HTTPException(status_code=404, detail="One or more products not found")

    total_price = 0.0
    for product in order_products:
        total_price += product.price

    order_id = str(uuid4())
    order = Order(
        order_id=order_id,
        customer_id=request.customer_id,
        order_date=datetime.utcnow(),
        total_price=total_price,
        status="Pending",
        products=order_products,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "order_date": order.order_date,
        "total_price": order.total_price,
        "status": order.status,
        "products": [p.product_id for p in order.products]
    }


# 3. Add products to an order
@app.post("/order/{order_id}/add-products", response_model=OrderResponse)
def add_product_to_order(order_id: str, request: AddProductsRequest, db: Session = Depends(get_db)):
    order = db.query(Order).filter_by(order_id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order with order-id {order_id} not found")

    # Get unique product_ids from the request
    new_product_ids = set(request.product_ids)

    # Fetch the actual Product objects
    products_to_add = db.query(Product).filter(Product.product_id.in_(new_product_ids)).all()

    # Check if all requested product_ids exist
    if len(products_to_add) != len(new_product_ids):
        raise HTTPException(status_code=404, detail="One or more products not found")

    # Combine existing and new products
    existing_product_ids = {product.product_id for product in order.products}
    all_products_set = {p.product_id: p for p in order.products}

    for product in products_to_add:
        all_products_set[product.product_id] = product  # Add or keep existing

    # Update order's products
    order.products = list(all_products_set.values())

    # Recalculate total price
    order.total_price = sum(p.price for p in order.products)

    db.commit()
    db.refresh(order)

    return {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "order_date": order.order_date,
        "total_price": order.total_price,
        "status": order.status.value,
        "products": [p.product_id for p in order.products]
    }


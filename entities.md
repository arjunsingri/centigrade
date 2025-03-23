Customer

customer_id (Primary Key)
first_name
last_name
email_address
phone_number
physical_address
creation_date

Product

product_id (Primary Key)
product_name
description
price
category

Order

order_id (Primary Key)
customer_id (Primary Key of Customer who placed the order)
order_date
total_price
status (e.g., Pending, Shipped, Delivered, Cancelled)
products (list of product_ids that are part of the order)

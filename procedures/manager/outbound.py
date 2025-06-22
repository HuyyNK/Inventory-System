import json
from database import get_db_connection, redis_client
from models.outbound_sql import get_outbounds, get_products, get_inventory_by_product, create_outbound

def get_outbounds_list():
    try:
        outbounds = get_outbounds()
        if not outbounds:
            return []
        return outbounds  # Dữ liệu đã được xử lý trong get_outbounds()
    except Exception as e:
        raise

def get_products_list(supplier_id=None):
    try:
        products = get_products(supplier_id)
        return products
    except Exception as e:
        raise

def get_inventory_for_product(product_id):
    try:
        inventory = get_inventory_by_product(product_id)
        return inventory
    except Exception as e:
        raise

def create_new_outbound(customer_name, date, created_by, notes, outbound_type, products):
    try:
        return create_outbound(customer_name, date, created_by, notes, outbound_type, products)
    except Exception as e:
        raise
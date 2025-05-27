from datetime import datetime, date
from models.outbound_sql import get_outbounds, get_products, get_inventory_by_product, create_outbound

def get_outbounds_list():
    try:
        outbounds = get_outbounds()
        if not outbounds:
            return []
        processed_outbounds = [
            {
                key: value.isoformat() if isinstance(value, (datetime, date)) else value
                for key, value in outbound.items()
            }
            for outbound in outbounds
        ]
        return processed_outbounds
    except Exception as e:
        raise

def get_products_list(supplier_id=None):
    try:
        return get_products(supplier_id)
    except Exception as e:
        raise

def get_inventory_for_product(product_id):
    try:
        return get_inventory_by_product(product_id)
    except Exception as e:
        raise

def create_new_outbound(customer_name, date, created_by, notes, outbound_type, products):
    try:
        return create_outbound(customer_name, date, created_by, notes, outbound_type, products)
    except Exception as e:
        raise
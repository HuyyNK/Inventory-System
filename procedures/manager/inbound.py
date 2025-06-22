import json
from database import get_db_connection, redis_client
from models.inbound_sql import get_inbounds, create_inbound, get_inbound_by_id
from datetime import datetime, date

def get_inbounds_list():
    try:
        inbounds = get_inbounds()
        if not inbounds:
            return []
        return inbounds  # Dữ liệu đã được xử lý thành chuỗi trong get_inbounds()
    except Exception as e:
        raise

def get_suppliers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, name FROM Supplier"
        cursor.execute(query)
        return cursor.fetchall() or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def get_products(supplier_id=None):
    cache_key = f"cache:products:{supplier_id}" if supplier_id else "cache:products"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if supplier_id:
            query = "SELECT id, name FROM Product WHERE supplier_id = %s"
            cursor.execute(query, (supplier_id,))
        else:
            query = "SELECT id, name FROM Product"
            cursor.execute(query)
        products = cursor.fetchall() or []
        redis_client.setex(cache_key, 300, json.dumps(products))
        return products
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def get_inbound_details(inbound_id: int):
    try:
        inbound_data = get_inbound_by_id(inbound_id)
        if not inbound_data:
            return None, []
        return inbound_data["inbound"], inbound_data["details"]  # Dữ liệu đã được xử lý
    except Exception as e:
        raise
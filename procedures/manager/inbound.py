from database import get_db_connection
from models.inbound_sql import get_inbounds, create_inbound, get_inbound_by_id
from datetime import datetime, date

def get_inbounds_list():
    try:
        inbounds = get_inbounds()
        if not inbounds:
            return []
        processed_inbounds = []
        for inbound in inbounds:
            processed_inbound = {
                key: value.isoformat() if isinstance(value, (datetime, date)) else value
                for key, value in inbound.items()
            }
            processed_inbounds.append(processed_inbound)
        return processed_inbounds
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
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if supplier_id:
            query = "SELECT id, name FROM Product WHERE supplier_id = %s"
            cursor.execute(query, (supplier_id,))
        else:
            query = "SELECT id, name FROM Product"
            cursor.execute(query)
        return cursor.fetchall() or []
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
        inbound = inbound_data["inbound"]
        details = inbound_data["details"]
        processed_details = [
            {
                key: value.isoformat() if isinstance(value, (datetime, date)) else value
                for key, value in detail.items()
            }
            for detail in details
        ]
        processed_inbound = {
            key: value.isoformat() if isinstance(value, (datetime, date)) else value
            for key, value in inbound.items()
        }
        return processed_inbound, processed_details
    except Exception as e:
        raise
from database import get_db_connection
from models.inbound_sql import get_inbounds, create_inbound
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

def get_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, name FROM Product"
        cursor.execute(query)
        return cursor.fetchall() or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()
import json
from database import get_db_connection, redis_client
from datetime import date, datetime

def get_inbounds():
    cache_key = "cache:inbound:list"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT i.id, i.date, i.total_amount, s.name AS supplier_name, u.full_name AS created_by_name
            FROM Inbound i
            LEFT JOIN Supplier s ON i.supplier_id = s.id
            LEFT JOIN User u ON i.created_by = u.id
            ORDER BY i.id DESC
        """
        cursor.execute(query)
        inbounds = cursor.fetchall()
        # Chuyển đổi date thành chuỗi trước khi lưu cache
        processed_inbounds = [
            {key: value.isoformat() if isinstance(value, (datetime, date)) else value
             for key, value in inbound.items()}
            for inbound in inbounds or []
        ]
        redis_client.setex(cache_key, 300, json.dumps(processed_inbounds))
        return processed_inbounds
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def create_inbound(supplier_id, date, created_by, notes, details):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("START TRANSACTION")
        query = """
            INSERT INTO Inbound (supplier_id, date, total_amount, created_by, notes, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (supplier_id, date, 0, created_by, notes, "Đã nhập"))
        inbound_id = cursor.lastrowid
        total_amount = 0

        for idx, detail in enumerate(details):
            product_id = detail.get('product_id')
            quantity = detail.get('quantity')
            unit_price = detail.get('unit_price')
            expiry_date = detail.get('expiry_date')
            manufacturing_date = detail.get('manufacturing_date')
            batch_number = detail.get('batch_number', f"LOT{datetime.now().strftime('%Y%m%d')}{idx}")
            detail_query = """
                INSERT INTO inbound_detail (inbound_id, product_id, quantity, unit_price, expiry_date, manufacturing_date, batch_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(detail_query, (inbound_id, product_id, quantity, unit_price, expiry_date, manufacturing_date, batch_number))
            total_amount += quantity * unit_price

            inventory_query = """
                INSERT INTO inventory (product_id, batch_number, current_quantity, expiry_date, last_updated)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(inventory_query, (product_id, batch_number, quantity, expiry_date, datetime.now()))

        update_query = "UPDATE Inbound SET total_amount = %s WHERE id = %s"
        cursor.execute(update_query, (total_amount, inbound_id))

        conn.commit()
        # Xóa cache sau khi cập nhật
        redis_client.delete("cache:inbound:list")
        return {"id": inbound_id, "total_amount": total_amount}
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def get_inbound_by_id(inbound_id: int):
    cache_key = f"cache:inbound:detail:{inbound_id}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT i.id, i.date, i.total_amount, i.notes, s.name AS supplier_name, u.full_name AS created_by_name
            FROM Inbound i
            LEFT JOIN Supplier s ON i.supplier_id = s.id
            LEFT JOIN User u ON i.created_by = u.id
            WHERE i.id = %s
        """
        cursor.execute(query, (inbound_id,))
        inbound = cursor.fetchone()
        if not inbound:
            return None

        detail_query = """
            SELECT id.product_id, p.name AS product_name, id.quantity, id.unit_price,
                   id.manufacturing_date, id.expiry_date, id.batch_number
            FROM inbound_detail id
            LEFT JOIN Product p ON id.product_id = p.id
            WHERE id.inbound_id = %s
        """
        cursor.execute(detail_query, (inbound_id,))
        details = cursor.fetchall() or []
        result = {
            "inbound": {key: value.isoformat() if isinstance(value, (datetime, date)) else value
                        for key, value in inbound.items()},
            "details": [{key: value.isoformat() if isinstance(value, (datetime, date)) else value
                         for key, value in detail.items()}
                        for detail in details]
        }
        redis_client.setex(cache_key, 300, json.dumps(result))
        return result
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()
import json
from database import get_db_connection, redis_client
from datetime import date, datetime
import time
import mysql.connector

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
    max_retries = 3
    retry_delay = 1  # Giây

    for attempt in range(max_retries):
        try:
            cursor.execute("START TRANSACTION")

            # Thêm bản ghi Inbound trước
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

                # Lock inventory record for the product
                lock_query = """
                    SELECT id, current_quantity FROM inventory 
                    WHERE product_id = %s AND batch_number = %s FOR UPDATE
                """
                cursor.execute(lock_query, (product_id, batch_number))
                locked_inventory = cursor.fetchone()

                if locked_inventory:
                    current_quantity = locked_inventory[1]
                    update_quantity = current_quantity + quantity
                else:
                    current_quantity = 0
                    update_quantity = quantity

                # Kiểm tra điều kiện (luôn >= 0 cho nhập kho)
                if update_quantity < 0:
                    raise ValueError("Số lượng tồn kho không hợp lệ sau cập nhật")

                # Cập nhật hoặc thêm bản ghi inventory
                if locked_inventory:
                    update_inventory_query = """
                        UPDATE inventory 
                        SET current_quantity = %s, last_updated = %s 
                        WHERE id = %s
                    """
                    cursor.execute(update_inventory_query, (update_quantity, datetime.now(), locked_inventory[0]))
                else:
                    insert_inventory_query = """
                        INSERT INTO inventory (product_id, batch_number, current_quantity, expiry_date, last_updated)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_inventory_query, (product_id, batch_number, quantity, expiry_date, datetime.now()))

                # Thêm chi tiết nhập kho
                detail_query = """
                    INSERT INTO inbound_detail (inbound_id, product_id, quantity, unit_price, expiry_date, manufacturing_date, batch_number)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(detail_query, (inbound_id, product_id, quantity, unit_price, expiry_date, manufacturing_date, batch_number))
                total_amount += quantity * unit_price

            # Cập nhật tổng tiền
            update_query = "UPDATE Inbound SET total_amount = %s WHERE id = %s"
            cursor.execute(update_query, (total_amount, inbound_id))

            conn.commit()
            # Xóa cache sau khi cập nhật
            redis_client.delete("cache:inbound:list")
            # Xóa cache dashboard liên quan
            redis_client.delete("cache:kpi:*")
            redis_client.delete("cache:charts:*")
            redis_client.delete("cache:warnings:*")
            redis_client.delete("cache:activities")
            return {"id": inbound_id, "total_amount": total_amount}

        except mysql.connector.errors.DatabaseError as db_error:
            conn.rollback()
            if attempt < max_retries - 1 and "deadlock" in str(db_error).lower():
                time.sleep(retry_delay * (attempt + 1))  # Tăng delay giữa các lần thử
                continue
            raise Exception("Xung đột dữ liệu, vui lòng thử lại sau.")
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
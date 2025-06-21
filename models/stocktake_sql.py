from database import get_db_connection
from datetime import datetime

def get_stocktakes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                s.id, 
                s.date, 
                s.status, 
                u.full_name AS created_by_name, 
                s.created_by,
                COALESCE(SUM(sd.variance_value), 0) AS total_variance_value
            FROM stocktake s
            LEFT JOIN user u ON s.created_by = u.id
            LEFT JOIN stocktake_detail sd ON s.id = sd.stocktake_id
            GROUP BY s.id, s.date, s.status, u.full_name, s.created_by
            ORDER BY s.id DESC
        """
        cursor.execute(query)
        stocktakes = cursor.fetchall()
        return stocktakes or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def get_inventory():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT i.id AS inventory_id, i.product_id, i.batch_number, i.current_quantity, i.expiry_date,
                   p.name, p.sku, p.cost_price
            FROM inventory i
            LEFT JOIN product p ON i.product_id = p.id
            WHERE i.current_quantity > 0
            ORDER BY p.id, i.expiry_date ASC
        """
        cursor.execute(query)
        inventory = cursor.fetchall()
        return inventory or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def get_product_id_from_inventory(inventory_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT product_id FROM inventory WHERE id = %s"
        cursor.execute(query, (inventory_id,))
        result = cursor.fetchone()
        return result["product_id"] if result else None
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def create_stocktake(date, created_by, status, items):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("START TRANSACTION")

        # Thêm bản ghi vào stocktake
        query = """
            INSERT INTO stocktake (date, created_by, status)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (date, created_by, status))
        stocktake_id = cursor.lastrowid

        # Thêm chi tiết vào stocktake_detail
        for item in items:
            if item["actual_quantity"] is None:
                continue

            # Lấy product_id từ inventory_id
            product_id = get_product_id_from_inventory(item["inventory_id"])
            if product_id is None:
                raise ValueError(f"Không tìm thấy product_id cho inventory_id {item['inventory_id']}")

            insert_detail_query = """
                INSERT INTO stocktake_detail (stocktake_id, inventory_id, product_id, system_quantity, 
                    actual_quantity, variance_type, variance_reason, variance_value)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_detail_query, (
                stocktake_id,
                item["inventory_id"],
                product_id,
                item["system_quantity"],
                item["actual_quantity"],
                item["variance_type"],
                item["variance_reason"],
                item["variance_value"]
            ))

            # Nếu trạng thái là "Đã kiểm kê", cập nhật tồn kho
            if status == "Đã kiểm kê":
                update_inventory_query = """
                    UPDATE inventory
                    SET current_quantity = %s, last_updated = %s
                    WHERE id = %s
                """
                cursor.execute(update_inventory_query, (
                    item["actual_quantity"],
                    datetime.now(),
                    item["inventory_id"]
                ))

        conn.commit()
        return {"id": stocktake_id}
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
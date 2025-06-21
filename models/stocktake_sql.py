from database import get_db_connection
from datetime import date, datetime

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
        print(f"get_product_id_from_inventory({inventory_id}) returned: {result}")
        if result is None:
            return None
        return result["product_id"]
    except Exception as e:
        print(f"Error in get_product_id_from_inventory: {e}")
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
            product_id = get_product_id_from_inventory(item["inventory_id"])
            if product_id is None:
                raise ValueError(f"Không tìm thấy product_id cho inventory_id {item['inventory_id']}")

            insert_detail_query = """
                INSERT INTO stocktake_detail (stocktake_id, inventory_id, product_id, system_quantity, 
                    actual_quantity, variance_type, variance_reason, variance_value)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Sử dụng variance_value từ frontend nếu có, nếu không thì tính lại
            variance_value = item.get("variance_value", (item["actual_quantity"] - item["system_quantity"]) * item.get("cost_price", 0))
            cursor.execute(insert_detail_query, (
                stocktake_id,
                item["inventory_id"],
                product_id,
                item["system_quantity"],
                item["actual_quantity"],
                item["variance_type"] or None,
                item["variance_reason"] or None,
                variance_value
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

def get_stocktake(stocktake_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                s.id, s.date, s.status, s.created_by, u.full_name AS created_by_name,
                sd.id AS detail_id, sd.inventory_id, sd.product_id, sd.system_quantity, 
                sd.actual_quantity, sd.variance, sd.variance_type, sd.variance_reason, 
                sd.variance_value, p.name, p.sku, i.batch_number, i.expiry_date
            FROM stocktake s
            LEFT JOIN user u ON s.created_by = u.id
            LEFT JOIN stocktake_detail sd ON s.id = sd.stocktake_id
            LEFT JOIN inventory i ON sd.inventory_id = i.id
            LEFT JOIN product p ON sd.product_id = p.id
            WHERE s.id = %s
        """
        cursor.execute(query, (stocktake_id,))
        results = cursor.fetchall()
        if not results:
            return None
        stocktake = {
            "id": results[0]["id"],
            "date": results[0]["date"].isoformat() if isinstance(results[0]["date"], (datetime, date)) else str(results[0]["date"]) if results[0]["date"] else None,
            "status": results[0]["status"],
            "created_by": results[0]["created_by"],
            "created_by_name": results[0]["created_by_name"],
            "details": []
        }
        for row in results:
            if row["detail_id"]:
                row["expiry_date"] = row["expiry_date"].isoformat() if row["expiry_date"] and isinstance(row["expiry_date"], (datetime, date)) else str(row["expiry_date"]) if row["expiry_date"] else None
                stocktake["details"].append(row)
        return stocktake
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def update_stocktake(stocktake_id, date, created_by, status, items):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION")

        # Cập nhật bản ghi stocktake
        update_stocktake_query = """
            UPDATE stocktake 
            SET date = %s, status = %s
            WHERE id = %s
        """
        cursor.execute(update_stocktake_query, (date, status, stocktake_id))

        # Lấy danh sách chi tiết hiện có để so sánh
        existing_details_query = "SELECT inventory_id FROM stocktake_detail WHERE stocktake_id = %s"
        cursor.execute(existing_details_query, (stocktake_id,))
        existing_inventory_ids = {row["inventory_id"] for row in cursor.fetchall()}

        # Chỉ xóa các chi tiết không còn trong items
        for inventory_id in existing_inventory_ids:
            if not any(item.get("inventory_id") == inventory_id for item in items if item.get("actual_quantity") is not None):
                delete_detail_query = "DELETE FROM stocktake_detail WHERE stocktake_id = %s AND inventory_id = %s"
                cursor.execute(delete_detail_query, (stocktake_id, inventory_id))

        # Thêm hoặc cập nhật chi tiết
        for item in items:
            print(f"Processing item: {item}")
            if not isinstance(item, dict):
                raise ValueError(f"Dữ liệu item không hợp lệ, không phải dict: {item}")
            if item.get("actual_quantity") is None:
                continue
            product_id = get_product_id_from_inventory(item["inventory_id"])
            print(f"Retrieved product_id for inventory_id {item['inventory_id']}: {product_id}")
            if product_id is None:
                raise ValueError(f"Không tìm thấy product_id cho inventory_id {item['inventory_id']}")

            # Kiểm tra xem item đã tồn tại chưa
            check_query = "SELECT id FROM stocktake_detail WHERE stocktake_id = %s AND inventory_id = %s"
            cursor.execute(check_query, (stocktake_id, item["inventory_id"]))
            existing = cursor.fetchone()

            # Sử dụng variance_value từ frontend nếu có, nếu không thì tính lại
            variance_value = item.get("variance_value", (item["actual_quantity"] - item["system_quantity"]) * item.get("cost_price", 0))

            if existing:
                update_detail_query = """
                    UPDATE stocktake_detail 
                    SET system_quantity = %s, actual_quantity = %s, 
                        variance_type = %s, variance_reason = %s, variance_value = %s
                    WHERE stocktake_id = %s AND inventory_id = %s
                """
                cursor.execute(update_detail_query, (
                    item["system_quantity"],
                    item["actual_quantity"],
                    item["variance_type"] or None,
                    item["variance_reason"] or None,
                    variance_value,  # Sử dụng variance_value từ frontend
                    stocktake_id,
                    item["inventory_id"]
                ))
            else:
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
                    item["variance_type"] or None,
                    item["variance_reason"] or None,
                    variance_value  # Sử dụng variance_value từ frontend
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
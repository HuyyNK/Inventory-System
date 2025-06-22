import json
from database import get_db_connection, redis_client
from datetime import date, datetime
import time
import mysql.connector

def _convert_datetime(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type not serializable")

def get_stocktakes():
    cache_key = "cache:stocktakes"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

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
        for stocktake in stocktakes:
            if isinstance(stocktake["date"], (datetime, date)):
                stocktake["date"] = stocktake["date"].isoformat()
        redis_client.setex(cache_key, 300, json.dumps(stocktakes or [], default=_convert_datetime))
        return stocktakes or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def get_inventory():
    cache_key = "cache:inventory"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

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
        for item in inventory:
            if item["expiry_date"] is not None:
                if isinstance(item["expiry_date"], (datetime, date)):
                    item["expiry_date"] = item["expiry_date"].isoformat()
                else:
                    item["expiry_date"] = str(item["expiry_date"]) if item["expiry_date"] else None
            else:
                item["expiry_date"] = None
        redis_client.setex(cache_key, 300, json.dumps(inventory or [], default=_convert_datetime))
        return inventory or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def get_product_id_from_inventory(inventory_id):
    cache_key = f"cache:product_id:{inventory_id}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data) if cached_data != "null" else None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT product_id FROM inventory WHERE id = %s"
        cursor.execute(query, (inventory_id,))
        result = cursor.fetchone()
        product_id = result["product_id"] if result else None
        redis_client.setex(cache_key, 300, json.dumps(product_id) if product_id else "null")
        return product_id
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def create_stocktake(date, created_by, status, items):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            cursor.execute("START TRANSACTION")

            query = """
                INSERT INTO stocktake (date, created_by, status)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (date, created_by, status))
            stocktake_id = cursor.lastrowid

            if items and any(item.get("actual_quantity") is not None for item in items):
                inventory_ids = [item["inventory_id"] for item in items if item.get("actual_quantity") is not None]
                if inventory_ids:
                    lock_query = "SELECT id, current_quantity FROM inventory WHERE id IN (" + ",".join(["%s"] * len(inventory_ids)) + ") FOR UPDATE"
                    cursor.execute(lock_query, tuple(inventory_ids))
                    cursor.fetchall()

            for item in items:
                if item["actual_quantity"] is None:
                    continue
                product_id = get_product_id_from_inventory(item["inventory_id"])
                if product_id is None:
                    raise ValueError(f"Không tìm thấy product_id cho inventory_id {item['inventory_id']}")

                variance_value = item.get("variance_value", (item["actual_quantity"] - item["system_quantity"]) * item.get("cost_price", 0))
                if item["actual_quantity"] != item["system_quantity"] and not item.get("variance_type"):
                    raise ValueError(f"Thiếu loại hao hụt cho inventory_id {item['inventory_id']}")
                if item["actual_quantity"] != item["system_quantity"] and not item.get("variance_reason"):
                    raise ValueError(f"Thiếu lý do chênh lệch cho inventory_id {item['inventory_id']}")

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
                    variance_value
                ))

                if status == "Đã kiểm kê":
                    if item["actual_quantity"] < 0:
                        raise ValueError("Số lượng thực tế không hợp lệ")
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
            redis_client.delete("cache:stocktakes")
            redis_client.delete("cache:inventory")
            redis_client.delete(f"cache:stocktake:{stocktake_id}")
            redis_client.delete("cache:kpi:*")
            redis_client.delete("cache:charts:*")
            redis_client.delete("cache:warnings:*")
            redis_client.delete("cache:activities")
            return {"id": stocktake_id}

        except mysql.connector.errors.DatabaseError as db_error:
            conn.rollback()
            if attempt < max_retries - 1 and "deadlock" in str(db_error).lower():
                time.sleep(retry_delay * (attempt + 1))
                continue
            raise Exception("Xung đột dữ liệu, vui lòng thử lại sau.")
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

def get_stocktake(stocktake_id):
    cache_key = f"cache:stocktake:{stocktake_id}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

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
        redis_client.setex(cache_key, 300, json.dumps(stocktake, default=_convert_datetime))
        return stocktake
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def update_stocktake(stocktake_id, date, created_by, status, items):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            cursor.execute("START TRANSACTION")

            update_stocktake_query = """
                UPDATE stocktake 
                SET date = %s, status = %s
                WHERE id = %s
            """
            cursor.execute(update_stocktake_query, (date, status, stocktake_id))

            inventory_ids = [item["inventory_id"] for item in items if item.get("actual_quantity") is not None]
            if inventory_ids:
                lock_query = "SELECT id, current_quantity FROM inventory WHERE id IN (" + ",".join(["%s"] * len(inventory_ids)) + ") FOR UPDATE"
                cursor.execute(lock_query, tuple(inventory_ids))
                cursor.fetchall()

            existing_details_query = "SELECT inventory_id FROM stocktake_detail WHERE stocktake_id = %s"
            cursor.execute(existing_details_query, (stocktake_id,))
            existing_inventory_ids = {row["inventory_id"] for row in cursor.fetchall()}

            for inventory_id in existing_inventory_ids:
                if not any(item.get("inventory_id") == inventory_id for item in items if item.get("actual_quantity") is not None):
                    delete_detail_query = "DELETE FROM stocktake_detail WHERE stocktake_id = %s AND inventory_id = %s"
                    cursor.execute(delete_detail_query, (stocktake_id, inventory_id))

            for item in items:
                if item.get("actual_quantity") is None:
                    continue
                product_id = get_product_id_from_inventory(item["inventory_id"])
                if product_id is None:
                    raise ValueError(f"Không tìm thấy product_id cho inventory_id {item['inventory_id']}")

                variance_value = item.get("variance_value", (item["actual_quantity"] - item["system_quantity"]) * item.get("cost_price", 0))
                if item["actual_quantity"] != item["system_quantity"] and not item.get("variance_type"):
                    raise ValueError(f"Thiếu loại hao hụt cho inventory_id {item['inventory_id']}")
                if item["actual_quantity"] != item["system_quantity"] and not item.get("variance_reason"):
                    raise ValueError(f"Thiếu lý do chênh lệch cho inventory_id {item['inventory_id']}")

                check_query = "SELECT id FROM stocktake_detail WHERE stocktake_id = %s AND inventory_id = %s"
                cursor.execute(check_query, (stocktake_id, item["inventory_id"]))
                existing = cursor.fetchone()

                if existing:
                    if isinstance(existing, tuple):
                        existing_id = existing[0] if existing else None
                    else:
                        existing_id = existing.get("id") if existing else None

                    if existing_id:
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
                            variance_value,
                            stocktake_id,
                            item["inventory_id"]
                        ))
                    else:
                        pass
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
                        variance_value
                    ))

                if status == "Đã kiểm kê":
                    if item["actual_quantity"] < 0:
                        raise ValueError("Số lượng thực tế không hợp lệ")
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
            redis_client.delete("cache:stocktakes")
            redis_client.delete("cache:inventory")
            redis_client.delete(f"cache:stocktake:{stocktake_id}")
            redis_client.delete("cache:kpi:*")
            redis_client.delete("cache:charts:*")
            redis_client.delete("cache:warnings:*")
            redis_client.delete("cache:activities")
            return {"id": stocktake_id}

        except mysql.connector.errors.DatabaseError as db_error:
            conn.rollback()
            if attempt < max_retries - 1 and "deadlock" in str(db_error).lower():
                time.sleep(retry_delay * (attempt + 1))
                continue
            raise Exception("Xung đột dữ liệu, vui lòng thử lại sau.")
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
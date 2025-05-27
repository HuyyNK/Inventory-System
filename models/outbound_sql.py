from database import get_db_connection
from datetime import datetime

def get_outbounds():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT o.id, o.customer_name, o.total_amount, u.full_name AS created_by_name,
                   o.date, o.outbound_type
            FROM Outbound o
            LEFT JOIN User u ON o.created_by = u.id
            ORDER BY o.id DESC
        """
        cursor.execute(query)
        outbounds = cursor.fetchall()
        return outbounds or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def get_outbound_by_id(outbound_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT o.id, o.customer_name, o.date, o.total_amount, o.notes, o.outbound_type,
                   u.full_name AS created_by_name
            FROM Outbound o
            LEFT JOIN User u ON o.created_by = u.id
            WHERE o.id = %s
        """
        cursor.execute(query, (outbound_id,))
        outbound = cursor.fetchone()
        if not outbound:
            return None, []

        detail_query = """
            SELECT id.product_id, p.name AS product_name, p.unit, id.quantity, id.unit_price,
                   id.batch_number, id.expiry_date
            FROM outbound_detail id
            LEFT JOIN Product p ON id.product_id = p.id
            WHERE id.outbound_id = %s
        """
        cursor.execute(detail_query, (outbound_id,))
        details = cursor.fetchall() or []
        return outbound, details
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
            query = "SELECT id, name, market_price FROM Product WHERE supplier_id = %s"
            cursor.execute(query, (supplier_id,))
        else:
            query = "SELECT id, name, market_price FROM Product"
            cursor.execute(query)
        return cursor.fetchall() or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def get_inventory_by_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id, batch_number, current_quantity, expiry_date
            FROM inventory
            WHERE product_id = %s AND current_quantity > 0
            ORDER BY expiry_date ASC
        """
        cursor.execute(query, (product_id,))
        return cursor.fetchall() or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def create_outbound(customer_name, date, created_by, notes, outbound_type, products):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("START TRANSACTION")
        # Thêm bản ghi vào outbound
        query = """
            INSERT INTO Outbound (customer_name, date, total_amount, created_by, notes, outbound_type, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (customer_name, date, 0, created_by, notes, outbound_type, "Đã xuất"))
        outbound_id = cursor.lastrowid
        total_amount = 0
        outbound_details = []

        # Xử lý từng sản phẩm theo FIFO
        for product in products:
            product_id = product["product_id"]
            quantity = product["quantity"]
            unit_price = product["unit_price"]
            remaining_quantity = quantity

            inventory_items = get_inventory_by_product(product_id)
            if not inventory_items:
                raise ValueError(f"Không có tồn kho cho sản phẩm ID {product_id}")

            for inventory in inventory_items:
                inventory_id = inventory["id"]
                batch_number = inventory["batch_number"]
                current_quantity = inventory["current_quantity"]
                expiry_date = inventory["expiry_date"]

                if remaining_quantity <= 0:
                    break

                if current_quantity > 0:
                    used_quantity = min(remaining_quantity, current_quantity)
                    detail = {
                        "outbound_id": outbound_id,
                        "product_id": product_id,
                        "quantity": used_quantity,
                        "unit_price": unit_price,
                        "batch_number": batch_number,
                        "expiry_date": expiry_date
                    }
                    outbound_details.append(detail)
                    remaining_quantity -= used_quantity
                    total_amount += used_quantity * unit_price

                    # Cập nhật tồn kho
                    new_quantity = current_quantity - used_quantity
                    update_query = """
                        UPDATE inventory
                        SET current_quantity = %s, last_updated = %s
                        WHERE id = %s
                    """
                    cursor.execute(update_query, (new_quantity, datetime.now(), inventory_id))

                    if new_quantity == 0:
                        delete_query = "DELETE FROM inventory WHERE id = %s"
                        cursor.execute(delete_query, (inventory_id,))

            if remaining_quantity > 0:
                raise ValueError(f"Số lượng tồn kho không đủ cho sản phẩm ID {product_id}. Còn thiếu {remaining_quantity} đơn vị.")

        # Thêm chi tiết vào outbound_detail
        for detail in outbound_details:
            insert_detail_query = """
                INSERT INTO outbound_detail (outbound_id, product_id, quantity, unit_price, batch_number, expiry_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_detail_query, (
                detail["outbound_id"],
                detail["product_id"],
                detail["quantity"],
                detail["unit_price"],
                detail["batch_number"],
                detail["expiry_date"]
            ))

        # Cập nhật total_amount trong outbound
        update_query = "UPDATE Outbound SET total_amount = %s WHERE id = %s"
        cursor.execute(update_query, (total_amount, outbound_id))

        conn.commit()
        return {"id": outbound_id, "total_amount": total_amount}
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
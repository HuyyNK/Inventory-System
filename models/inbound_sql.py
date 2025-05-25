from database import get_db_connection
from datetime import datetime

def get_inbounds():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT i.id, i.date, i.total_amount, s.name AS supplier_name
            FROM Inbound i
            LEFT JOIN Supplier s ON i.supplier_id = s.id
            ORDER BY i.id DESC
        """
        cursor.execute(query)
        inbounds = cursor.fetchall()
        return inbounds or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def create_inbound(supplier_id, date, created_by, notes, details):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Bắt đầu transaction
        cursor.execute("START TRANSACTION")

        # Thêm phiếu nhập
        query = """
            INSERT INTO Inbound (supplier_id, date, total_amount, created_by, notes, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (supplier_id, date, 0, created_by, notes, "Đã nhập"))
        inbound_id = cursor.lastrowid

        # Thêm chi tiết phiếu nhập
        total_amount = 0
        for detail in details:
            product_id = detail.get('product_id')
            quantity = detail.get('quantity')
            unit_price = detail.get('unit_price')
            expiry_date = detail.get('expiry_date')
            manufacturing_date = detail.get('manufacturing_date')
            batch_number = detail.get('batch_number', '')

            detail_query = """
                INSERT INTO inbound_detail (inbound_id, product_id, quantity, unit_price, expiry_date, manufacturing_date, batch_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(detail_query, (inbound_id, product_id, quantity, unit_price, expiry_date, manufacturing_date, batch_number))
            total_amount += quantity * unit_price

        # Cập nhật tổng tiền
        update_query = "UPDATE Inbound SET total_amount = %s WHERE id = %s"
        cursor.execute(update_query, (total_amount, inbound_id))

        # Cập nhật inventory
        for detail in details:
            product_id = detail.get('product_id')
            quantity = detail.get('quantity')
            cursor.execute("""
                INSERT INTO inventory (product_id, current_quantity)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE current_quantity = current_quantity + %s
            """, (product_id, quantity, quantity))

        conn.commit()
        return {"id": inbound_id, "total_amount": total_amount}
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
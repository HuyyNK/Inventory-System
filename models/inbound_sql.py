from database import get_db_connection
from datetime import datetime

def get_inbounds():
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
        cursor.execute("START TRANSACTION")
        # Thêm bản ghi vào inbound với ngày hiện tại
        query = """
            INSERT INTO Inbound (supplier_id, date, total_amount, created_by, notes, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (supplier_id, date, 0, created_by, notes, "Đã nhập"))
        inbound_id = cursor.lastrowid
        total_amount = 0

        # Thêm chi tiết nhập vào inbound_detail
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

            # Thêm bản ghi mới vào inventory cho mỗi lô
            inventory_query = """
                INSERT INTO inventory (product_id, batch_number, current_quantity, expiry_date, last_updated)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(inventory_query, (product_id, batch_number, quantity, expiry_date, datetime.now()))

        # Cập nhật total_amount trong inbound
        update_query = "UPDATE Inbound SET total_amount = %s WHERE id = %s"
        cursor.execute(update_query, (total_amount, inbound_id))

        conn.commit()
        return {"id": inbound_id, "total_amount": total_amount}
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def get_inbound_by_id(inbound_id: int):
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
        return {"inbound": inbound, "details": details}
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()
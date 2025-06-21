from database import get_db_connection
from datetime import datetime, timedelta
from decimal import Decimal

def fetch_kpi(expiry_threshold):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            WITH loss_calc AS (
                SELECT COALESCE(
                    (SUM(CASE WHEN sd.variance < 0 THEN -sd.variance_value ELSE 0 END) / 
                     NULLIF(SUM(sd.system_quantity * p.cost_price), 0) * 100), 0) AS loss
                FROM stocktake_detail sd
                JOIN stocktake s ON sd.stocktake_id = s.id
                JOIN inventory i ON sd.inventory_id = i.id
                JOIN product p ON sd.product_id = p.id
                WHERE s.date = (SELECT MAX(date) FROM stocktake WHERE date IS NOT NULL)
            )
            SELECT 
                SUM(i.current_quantity) AS total_quantity,
                SUM(i.current_quantity * p.cost_price) AS total_value,
                COUNT(CASE WHEN i.current_quantity <= p.min_stock THEN 1 END) AS low_stock,
                COUNT(CASE WHEN i.expiry_date <= %s THEN 1 END) AS expiring,
                COALESCE((SELECT loss FROM loss_calc), 0) AS loss_percentage
            FROM inventory i
            JOIN product p ON i.product_id = p.id
        """
        cursor.execute(query, (expiry_threshold,))
        result = cursor.fetchone() or {
            "total_quantity": 0,
            "total_value": 0.0,
            "low_stock": 0,
            "expiring": 0,
            "loss_percentage": 0.0
        }
        # Chuyển đổi Decimal sang int/float
        result["total_quantity"] = int(result["total_quantity"] or 0)
        result["total_value"] = float(result["total_value"] or 0)
        result["low_stock"] = int(result["low_stock"] or 0)
        result["expiring"] = int(result["expiring"] or 0)
        result["loss_percentage"] = float(result["loss_percentage"] or 0)
        return result
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def fetch_charts(six_months_ago, one_month_ago):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Pie Chart: Tồn kho theo danh mục
        pie_query = """
            SELECT c.name, SUM(i.current_quantity) AS total_quantity
            FROM inventory i
            JOIN product p ON i.product_id = p.id
            JOIN category c ON p.category_id = c.id
            GROUP BY c.id, c.name
            ORDER BY total_quantity DESC
            LIMIT 5
        """
        cursor.execute(pie_query)
        pie_data = cursor.fetchall()
        pie_labels = [row["name"] for row in pie_data] or ["Không có dữ liệu"]
        pie_values = [int(row["total_quantity"]) for row in pie_data] or [0]

        # Line Chart: Xu hướng nhập/xuất kho
        line_query = """
            SELECT DATE_FORMAT(i.date, '%Y-%m') AS month, 
                   SUM(i.total_amount) AS inbound_value, 
                   0 AS outbound_value
            FROM inbound i
            WHERE i.date >= %s
            GROUP BY month
            UNION
            SELECT DATE_FORMAT(o.date, '%Y-%m') AS month, 
                   0 AS inbound_value, 
                   SUM(o.total_amount) AS outbound_value
            FROM outbound o
            WHERE o.date >= %s
            GROUP BY month
            ORDER BY month
        """
        cursor.execute(line_query, (six_months_ago, six_months_ago))
        line_data = cursor.fetchall()
        month_dict = {}
        for row in line_data:
            month = row["month"]
            if month not in month_dict:
                month_dict[month] = {"inbound": 0, "outbound": 0}
            month_dict[month]["inbound"] += row["inbound_value"]
            month_dict[month]["outbound"] += row["outbound_value"]
        line_labels = sorted(month_dict.keys()) or [six_months_ago.strftime("%Y-%m")]
        inbound_data = [float(month_dict[label]["inbound"]) for label in line_labels] or [0]
        outbound_data = [float(month_dict[label]["outbound"]) for label in line_labels] or [0]

        # Bar Chart: Top 5 sản phẩm bán chạy
        bar_query = """
            SELECT p.name, SUM(od.quantity) AS total_quantity
            FROM outbound_detail od
            JOIN product p ON od.product_id = p.id
            JOIN outbound o ON od.outbound_id = o.id
            WHERE o.date >= %s
            GROUP BY p.id, p.name
            ORDER BY total_quantity DESC
            LIMIT 5
        """
        cursor.execute(bar_query, (one_month_ago,))
        bar_data = cursor.fetchall()
        bar_labels = [row["name"] for row in bar_data] or ["Không có dữ liệu"]
        bar_values = [int(row["total_quantity"]) for row in bar_data] or [0]

        # Stacked Bar Chart: Tình trạng kho lưu trữ
        stacked_query = """
            SELECT p.storage_location, SUM(i.current_quantity) AS total_quantity
            FROM inventory i
            JOIN product p ON i.product_id = p.id
            GROUP BY p.storage_location
        """
        cursor.execute(stacked_query)
        stacked_data = cursor.fetchall()
        stacked_labels = [row["storage_location"] or "Không xác định" for row in stacked_data] or ["Không xác định"]
        stacked_values = [int(row["total_quantity"]) for row in stacked_data] or [0]

        return {
            "pie_labels": pie_labels,
            "pie_values": pie_values,
            "line_labels": line_labels,
            "inbound_data": inbound_data,
            "outbound_data": outbound_data,
            "bar_labels": bar_labels,
            "bar_values": bar_values,
            "stacked_labels": stacked_labels,
            "stacked_values": stacked_values
        }
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def fetch_warnings(expiry_threshold, last_date):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                p.name, 
                i.batch_number, 
                i.current_quantity, 
                i.expiry_date,
                i.id AS inventory_id,
                CASE 
                    WHEN i.expiry_date <= %s AND i.current_quantity <= p.min_stock THEN 'Sắp hết hạn và dưới mức tối thiểu'
                    WHEN i.expiry_date <= %s THEN 'Sắp hết hạn'
                    WHEN i.current_quantity <= p.min_stock THEN 'Dưới mức tối thiểu'
                END AS status,
                CASE 
                    WHEN i.expiry_date <= %s AND i.current_quantity <= p.min_stock THEN 'Tạo phiếu xuất và nhập'
                    WHEN i.expiry_date <= %s THEN 'Tạo phiếu xuất'
                    WHEN i.current_quantity <= p.min_stock THEN 'Tạo phiếu nhập'
                END AS action
            FROM inventory i
            JOIN product p ON i.product_id = p.id
            WHERE i.expiry_date <= %s OR i.current_quantity <= p.min_stock
            UNION
            SELECT 
                p.name, 
                i.batch_number, 
                i.current_quantity, 
                i.expiry_date,
                i.id AS inventory_id,
                'Chênh lệch kiểm kê' AS status,
                'Xem chi tiết' AS action
            FROM stocktake_detail sd
            JOIN inventory i ON sd.inventory_id = i.id
            JOIN product p ON sd.product_id = p.id
            JOIN stocktake s ON sd.stocktake_id = s.id
            WHERE sd.variance <> 0 AND s.date = %s
            GROUP BY i.id, p.name, i.batch_number, i.current_quantity, i.expiry_date
            LIMIT 10
        """
        cursor.execute(query, (expiry_threshold, expiry_threshold, expiry_threshold, expiry_threshold, expiry_threshold, last_date))
        warnings = cursor.fetchall() or []
        return [{
            "name": row["name"],
            "batch_number": row["batch_number"],
            "current_quantity": int(row["current_quantity"]),
            "expiry_date": row["expiry_date"].isoformat() if row["expiry_date"] else None,
            "status": row["status"],
            "action": row["action"],
            "inventory_id": int(row["inventory_id"]) if row["inventory_id"] else None
        } for row in warnings]
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def fetch_activities():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                'Nhập kho' AS activity_type, 
                i.date, 
                CONCAT('INB-', LPAD(i.id, 3, '0')) AS code, 
                u.full_name, 
                CONCAT('Nhập ', SUM(id.quantity), ' sản phẩm từ ', COALESCE(s.name, 'Nhà cung cấp không xác định')) AS description,
                NULL AS stocktake_id
            FROM inbound i
            JOIN user u ON i.created_by = u.id
            JOIN supplier s ON i.supplier_id = s.id
            JOIN inbound_detail id ON i.id = id.inbound_id
            GROUP BY i.id
            UNION
            SELECT 
                'Xuất kho' AS activity_type, 
                o.date, 
                CONCAT('OUT-', LPAD(o.id, 3, '0')) AS code, 
                u.full_name, 
                CONCAT('Xuất ', SUM(od.quantity), ' sản phẩm cho ', COALESCE(o.customer_name, 'Khách không xác định')) AS description,
                NULL AS stocktake_id
            FROM outbound o
            JOIN user u ON o.created_by = u.id
            JOIN outbound_detail od ON o.id = od.outbound_id
            GROUP BY o.id
            UNION
            SELECT 
                'Kiểm kê' AS activity_type, 
                s.date, 
                CONCAT('STK-', LPAD(s.id, 3, '0')) AS code, 
                u.full_name, 
                CONCAT('Kiểm kê kho, trạng thái: ', s.status) AS description,
                s.id AS stocktake_id
            FROM stocktake s
            JOIN user u ON s.created_by = u.id
            ORDER BY date DESC
            LIMIT 10
        """
        cursor.execute(query)
        activities = cursor.fetchall() or []
        return [{
            "date": row["date"].isoformat() if row["date"] else None,
            "activity_type": row["activity_type"],
            "code": row["code"],
            "full_name": row["full_name"],
            "description": row["description"],
            "stocktake_id": int(row["stocktake_id"]) if row.get("stocktake_id") else None
        } for row in activities]
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()
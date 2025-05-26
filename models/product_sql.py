from database import get_db_connection
from datetime import datetime

def get_products_sql(product_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT p.id, p.sku, p.name, p.unit, p.description, p.cost_price, p.market_price,
                p.min_stock, p.max_stock, p.storage_location, p.created_at, p.updated_at,
                c.name AS category_name, c.id AS category_id,
                s.name AS supplier_name, s.id AS supplier_id,
                COALESCE(SUM(i.current_quantity), 0) AS current_quantity
            FROM product p
            LEFT JOIN category c ON p.category_id = c.id
            LEFT JOIN supplier s ON p.supplier_id = s.id
            LEFT JOIN inventory i ON p.id = i.product_id
        """
        params = []
        if product_id:
            query += " WHERE p.id = %s"
            params = (product_id,)
        query += " GROUP BY p.id, c.name, c.id, s.name, s.id"
        cursor.execute(query, params)
        products = cursor.fetchall() if not product_id else cursor.fetchone()
        return products or []
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def get_inbound_details_sql(product_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id.id, id.inbound_id, id.batch_number, id.quantity, id.unit_price,
                (id.quantity * id.unit_price) AS total_amount,
                id.manufacturing_date, id.expiry_date,
                i.current_quantity, i.batch_number AS inventory_batch_number,
                i.expiry_date AS inventory_expiry_date
            FROM inbound_detail id
            LEFT JOIN inventory i ON id.product_id = i.product_id AND id.batch_number = i.batch_number
            WHERE id.product_id = %s
            ORDER BY id.inbound_id, id.batch_number
        """
        cursor.execute(query, (product_id,))
        details = cursor.fetchall()
        # Convert date fields to datetime objects
        for detail in details:
            if detail['manufacturing_date']:
                detail['manufacturing_date'] = datetime.strptime(str(detail['manufacturing_date']), '%Y-%m-%d')
            if detail['expiry_date']:
                detail['expiry_date'] = datetime.strptime(str(detail['expiry_date']), '%Y-%m-%d')
            if detail['inventory_expiry_date']:
                detail['inventory_expiry_date'] = datetime.strptime(str(detail['inventory_expiry_date']), '%Y-%m-%d')
        return details
    except Exception as e:
        raise
    finally:
        cursor.close()
        conn.close()

def add_product_sql(sku, name, unit, description, cost_price, market_price, min_stock, max_stock, storage_location, supplier_id, category_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Product (sku, name, unit, description, cost_price, market_price, min_stock, max_stock, storage_location, supplier_id, category_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (sku, name, unit, description, cost_price, market_price, min_stock, max_stock, storage_location, supplier_id, category_id)
        )
        product_id = cursor.lastrowid
        conn.commit()
        return product_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def update_product_sql(product_id, product_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE Product
            SET name = %s, unit = %s, description = %s, cost_price = %s, market_price = %s,
                min_stock = %s, max_stock = %s, storage_location = %s, supplier_id = %s, category_id = %s
            WHERE id = %s
            """,
            (
                product_data["name"],
                product_data["unit"],
                product_data["description"],
                product_data["cost_price"],
                product_data["market_price"],
                product_data["min_stock"],
                product_data["max_stock"],
                product_data["storage_location"],
                product_data["supplier_id"],
                product_data["category_id"],
                product_id
            )
        )
        conn.commit()
        return product_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_max_sku():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT MAX(sku) AS max_sku FROM Product")
        result = cursor.fetchone()
        return result["max_sku"] if result and result["max_sku"] else None
    except Exception as e:
        raise e
    finally:
        cursor.close()
        conn.close()
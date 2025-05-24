from database import get_db_connection
from datetime import datetime


def get_products_sql(product_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT p.id, p.sku, p.name, p.unit, p.description, p.cost_price, p.market_price,
                p.min_stock, p.max_stock, p.storage_location,
                c.name AS category_name, c.id AS category_id,
                s.name AS supplier_name, s.id AS supplier_id,
                i.current_quantity
            FROM product p
            LEFT JOIN category c ON p.category_id = c.id
            LEFT JOIN supplier s ON p.supplier_id = s.id
            LEFT JOIN inventory i ON p.id = i.product_id
        """
        params = ()
        if product_id:
            query += " WHERE p.id = %s"
            params = (product_id,)
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
    query = """
        SELECT id.id, id.inbound_id, id.batch_number, id.quantity, id.unit_price,
               (id.quantity * id.unit_price) AS total_amount,
            id.manufacturing_date, id.expiry_date,
            i.current_quantity
        FROM inbound_detail id
        LEFT JOIN inventory i ON id.product_id = i.product_id
        WHERE id.product_id = %s
    """
    cursor.execute(query, (product_id,))
    details = cursor.fetchall()
    cursor.close()
    conn.close()
    # Convert date fields to datetime objects
    for detail in details:
        if detail['manufacturing_date']:
            detail['manufacturing_date'] = datetime.strptime(str(detail['manufacturing_date']), '%Y-%m-%d')
        if detail['expiry_date']:
            detail['expiry_date'] = datetime.strptime(str(detail['expiry_date']), '%Y-%m-%d')
    return details

def add_product_sql(sku, name, unit, description, cost_price, market_price, min_stock, max_stock, storage_location, supplier_id, category_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Product (sku, name, unit, description, cost_price, market_price, min_stock, max_stock, storage_location, supplier_id, category_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (sku, name, unit, description, cost_price, market_price, min_stock, max_stock, storage_location, supplier_id, category_id)
    )
    product_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return product_id

def update_product_sql(product_id, product_data):
    conn = get_db_connection()
    cursor = conn.cursor()
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
    cursor.close()
    conn.close()
    return product_id

def get_max_sku():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT MAX(sku) AS max_sku FROM Product")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result["max_sku"] if result and result["max_sku"] else None
from database import get_db_connection

def get_products_sql(product_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT p.id, p.sku, p.name, p.unit, p.storage_location,
            c.name AS category_name,
            s.name AS supplier_name,
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
    cursor.close()
    conn.close()
    return products

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

def get_max_sku():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT MAX(sku) AS max_sku FROM Product")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result["max_sku"] if result and result["max_sku"] else None
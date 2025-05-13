from database import get_db_connection

def get_categories_sql():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM Category")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": c[0], "name": c[1], "description": c[2]} for c in categories]

def delete_category_sql(category_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Category WHERE id = %s", (category_id,))
    affected_rows = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected_rows > 0

def add_category_sql(name: str, description: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Category (name, description) VALUES (%s, %s)",
        (name, description)
    )
    category_id = cursor.lastrowid  # Lấy ID của danh mục vừa thêm
    conn.commit()
    cursor.close()
    conn.close()
    return category_id

def update_category_sql(category_id: int, name: str, description: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Category SET name = %s, description = %s WHERE id = %s",
        (name, description, category_id)
    )
    affected_rows = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected_rows > 0

def get_category_by_id_sql(category_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM Category WHERE id = %s", (category_id,))
    category = cursor.fetchone()
    cursor.close()
    conn.close()
    if category:
        return {"id": category[0], "name": category[1], "description": category[2]}
    return None
from database import get_db_connection

def get_suppliers_sql():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, email, address FROM supplier")
    suppliers = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": s[0], "name": s[1], "phone": s[2], "email": s[3], "address": s[4]} for s in suppliers]

def delete_supplier_sql(supplier_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM supplier WHERE id = %s", (supplier_id,))
    affected_rows = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected_rows > 0

def add_supplier_sql(name: str, phone: str, email: str, address: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO supplier (name, phone, email, address) VALUES (%s, %s, %s, %s)",
        (name, phone, email, address)
    )
    supplier_id = cursor.lastrowid  # Lấy ID của nhà cung cấp vừa thêm
    conn.commit()
    cursor.close()
    conn.close()
    return supplier_id

def update_supplier_sql(supplier_id: int, name: str, phone: str, email: str, address: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE supplier SET name = %s, phone = %s, email = %s, address = %s WHERE id = %s",
        (name, phone, email, address, supplier_id)
    )
    affected_rows = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected_rows > 0

def get_supplier_by_id_sql(supplier_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, email, address FROM supplier WHERE id = %s", (supplier_id,))
    supplier = cursor.fetchone()
    cursor.close()
    conn.close()
    if supplier:
        return {"id": supplier[0], "name": supplier[1], "phone": supplier[2], "email": supplier[3], "address": supplier[4]}
    return None
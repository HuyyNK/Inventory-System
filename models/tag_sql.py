from database import get_db_connection

def get_tags_sql():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, storage_location, created_at FROM tag")
    tags = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": t[0], "name":

 t[1], "description": t[2], "storage_location": t[3], "created_at": str(t[4])} for t in tags]

def get_tag_by_id_sql(tag_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, storage_location, created_at FROM tag WHERE id = %s", (tag_id,))
    tag = cursor.fetchone()
    cursor.close()
    conn.close()
    if tag:
        return {"id": tag[0], "name": tag[1], "description": tag[2], "storage_location": tag[3], "created_at": str(tag[4])}
    return None

def add_tag_sql(name: str, description: str, storage_location: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tag (name, description, storage_location) VALUES (%s, %s, %s)",
        (name, description, storage_location)
    )
    tag_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return tag_id

def update_tag_sql(tag_id: int, name: str, description: str, storage_location: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tag SET name = %s, description = %s, storage_location = %s WHERE id = %s",
        (name, description, storage_location, tag_id)
    )
    affected_rows = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected_rows > 0

def delete_tag_sql(tag_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tag WHERE id = %s", (tag_id,))
    affected_rows = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected_rows > 0
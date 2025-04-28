from database import get_db_connection

def get_user_by_username_sql(username: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT u.id, u.username, u.password, u.full_name, u.phone, u.email, u.address, u.birthday, 
               u.gender, u.is_active, u.role_id, r.name as role_name
        FROM user u
        LEFT JOIN role r ON u.role_id = r.id
        WHERE u.username = %s
        """,
        (username,)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and user["birthday"]:
        user["birthday"] = user["birthday"].strftime("%Y-%m-%d")  # Chuyển đổi date thành chuỗi
    return user

# Hàm lấy role_name
def get_role_name(role_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM role WHERE id = %s", (role_id,))
    role = cursor.fetchone()
    cursor.close()
    conn.close()
    return role[0] if role else "Unknown"  # Truy cập cột "name" bằng chỉ số 0

# Hàm cập nhật thông tin người dùng
def update_user_sql(user_id: int, full_name: str, phone: str, email: str, address: str, birthday: str, gender: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE user
        SET full_name = %s, phone = %s, email = %s, address = %s, birthday = %s, gender = %s
        WHERE id = %s
        """,
        (
            full_name,
            phone,
            email,
            address,
            birthday,
            gender,
            user_id,
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()
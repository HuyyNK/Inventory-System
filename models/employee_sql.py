from database import get_db_connection

def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT u.id, u.username, u.full_name, u.phone, u.email, u.is_active, r.name AS role_name
            FROM user u
            LEFT JOIN role r ON u.role_id = r.id
            """
        )
        employees = cursor.fetchall()
        return employees or []
    except Exception as e:
        raise e
    finally:
        cursor.close()
        conn.close()

def get_employee_by_id(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT u.*, r.name AS role_name
            FROM user u
            LEFT JOIN role r ON u.role_id = r.id
            WHERE u.id = %s
            """,
            (user_id,)
        )
        employee = cursor.fetchone()
        return employee
    except Exception as e:
        raise e
    finally:
        cursor.close()
        conn.close()

def get_roles():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM role")
        roles = cursor.fetchall()
        return roles or []
    except Exception as e:
        raise e
    finally:
        cursor.close()
        conn.close()

def check_username_exists(username: str, exclude_user_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if exclude_user_id is not None:
            cursor.execute("SELECT id FROM user WHERE username = %s AND id != %s", (username, exclude_user_id))
        else:
            cursor.execute("SELECT id FROM user WHERE username = %s", (username,))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        raise e
    finally:
        cursor.close()
        conn.close()

def check_email_exists(email: str, exclude_user_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if exclude_user_id is not None:
            cursor.execute("SELECT id FROM user WHERE email = %s AND id != %s", (email, exclude_user_id))
        else:
            cursor.execute("SELECT id FROM user WHERE email = %s", (email,))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        raise e
    finally:
        cursor.close()
        conn.close()

def add_employee(employee_data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO user (username, password, full_name, phone, email, address, birthday, gender, is_active, role_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                employee_data['username'],
                employee_data['password'],
                employee_data['full_name'],
                employee_data['phone'],
                employee_data['email'],
                employee_data['address'],
                employee_data['birthday'],
                employee_data['gender'],
                employee_data['is_active'],
                employee_data['role_id'],
            )
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def update_employee(user_id: int, employee_data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE user
            SET username = %s, password = %s, full_name = %s, phone = %s, email = %s,
                address = %s, birthday = %s, gender = %s, is_active = %s, role_id = %s
            WHERE id = %s
            """,
            (
                employee_data['username'],
                employee_data['password'],
                employee_data['full_name'],
                employee_data['phone'],
                employee_data['email'],
                employee_data['address'],
                employee_data['birthday'],
                employee_data['gender'],
                employee_data['is_active'],
                employee_data['role_id'],
                user_id,
            )
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

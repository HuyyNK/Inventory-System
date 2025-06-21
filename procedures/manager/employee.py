from models.employee_sql import get_employees, get_roles, check_username_exists, check_email_exists, add_employee, get_employee_by_id, update_employee

def get_employees_processed():
    try:
        employees = get_employees()
        if not employees:
            return []
        processed_employees = []
        for employee in employees:
            processed_employee = {
                key: value
                for key, value in employee.items()
            }
            processed_employee['status'] = 'Hoạt động' if employee.get('is_active') == 1 else 'Không hoạt động'
            processed_employees.append(processed_employee)
        return processed_employees
    except Exception as e:
        raise e

def get_roles_processed():
    try:
        roles = get_roles()
        return roles or []
    except Exception as e:
        raise e

def get_employee_processed(user_id: int):
    try:
        employee = get_employee_by_id(user_id)
        if employee:
            employee['status'] = 'Hoạt động' if employee.get('is_active') == 1 else 'Không hoạt động'
        return employee
    except Exception as e:
        raise e

def add_employee_processed(employee_data: dict):
    try:
        required_fields = ['full_name', 'username', 'password', 'role_id', 'phone', 'email', 'address', 'birthday', 'gender']
        for field in required_fields:
            if not employee_data.get(field):
                raise ValueError(f"Trường {field} là bắt buộc.")
        if check_username_exists(employee_data['username']):
            raise ValueError("Tên đăng nhập đã tồn tại.")
        if employee_data['email'] and check_email_exists(employee_data['email']):
            raise ValueError("Email đã tồn tại.")
        success = add_employee(employee_data)
        return success
    except Exception as e:
        raise e

def update_employee_processed(user_id: int, employee_data: dict, current_employee: dict):
    try:
        required_fields = ['full_name', 'username', 'role_id', 'phone', 'email', 'address', 'birthday', 'gender']
        for field in required_fields:
            if not employee_data.get(field):
                raise ValueError(f"Trường {field} là bắt buộc.")
        if check_username_exists(employee_data['username'], exclude_user_id=user_id):
            raise ValueError("Tên đăng nhập đã tồn tại.")
        if employee_data['email'] and check_email_exists(employee_data['email'], exclude_user_id=user_id):
            raise ValueError("Email đã tồn tại.")
        if not employee_data['password']:
            employee_data['password'] = current_employee['password']
        else:
            employee_data['password'] = employee_data['password']
        success = update_employee(user_id, employee_data)
        return success
    except Exception as e:
        raise e

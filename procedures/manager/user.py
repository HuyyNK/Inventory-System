from models.user_sql import get_role_name, update_user_sql

def get_user_details(user: dict) -> dict:
    user_data = user.copy()
    user_data["role_name"] = get_role_name(user["role_id"])
    return user_data

def update_user(user_id: int, full_name: str, phone: str, email: str, address: str, birthday: str, gender: str):
    update_user_sql(
        user_id=user_id,
        full_name=full_name,
        phone=phone if phone else None,
        email=email if email else None,
        address=address if address else None,
        birthday=birthday if birthday else None,
        gender=gender if gender else None
    )
from fastapi import HTTPException
from models.user_sql import get_role_name, update_user_sql, get_user_by_id_sql, update_user_password_sql

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
    
def change_password(user_id: int, old_password: str, new_password: str):
    user = get_user_by_id_sql(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["password"] != old_password:
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    update_user_password_sql(user_id, new_password)
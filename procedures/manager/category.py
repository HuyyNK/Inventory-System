from models.category_sql import get_categories_sql, delete_category_sql, add_category_sql, update_category_sql, get_category_by_id_sql

def get_categories():
    return get_categories_sql()

def delete_category(category_id: int):
    return delete_category_sql(category_id)

def add_category(name: str, description: str):
    category_id = add_category_sql(name, description)
    return {"id": category_id, "name": name, "description": description}

def update_category(category_id: int, name: str, description: str):
    return update_category_sql(category_id, name, description)

def get_category_by_id(category_id: int):
    return get_category_by_id_sql(category_id)
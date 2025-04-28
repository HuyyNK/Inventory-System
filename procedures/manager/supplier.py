from models.supplier_sql import get_suppliers_sql, delete_supplier_sql, add_supplier_sql, update_supplier_sql, get_supplier_by_id_sql

def get_suppliers():
    return get_suppliers_sql()

def delete_supplier(supplier_id: int):
    return delete_supplier_sql(supplier_id)

def add_supplier(name: str, phone: str, email: str, address: str):
    supplier_id = add_supplier_sql(name, phone, email, address)
    return {"id": supplier_id, "name": name, "phone": phone, "email": email, "address": address}

def update_supplier(supplier_id: int, name: str, phone: str, email: str, address: str):
    return update_supplier_sql(supplier_id, name, phone, email, address)

def get_supplier_by_id(supplier_id: int):
    return get_supplier_by_id_sql(supplier_id)
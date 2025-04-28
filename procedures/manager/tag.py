from models.tag_sql import get_tags_sql, get_tag_by_id_sql, add_tag_sql, update_tag_sql, delete_tag_sql

def get_tags():
    return get_tags_sql()

def get_tag_by_id(tag_id: int):
    return get_tag_by_id_sql(tag_id)

def add_tag(name: str, description: str, storage_location: str):
    tag_id = add_tag_sql(name, description, storage_location)
    return {"id": tag_id, "name": name, "description": description, "storage_location": storage_location}

def update_tag(tag_id: int, name: str, description: str, storage_location: str):
    return update_tag_sql(tag_id, name, description, storage_location)

def delete_tag(tag_id: int):
    return delete_tag_sql(tag_id)
from models.product_sql import get_products_sql, add_product_sql, get_max_sku
from pathlib import Path
from database import get_db_connection

def get_products():
    products = get_products_sql()
    if not products:
        return []
    return products

def get_next_sku():
    try:
        max_sku = get_max_sku()
        if not max_sku:
            return "SKU000001"
        num = int(max_sku.replace("SKU", "")) + 1
        return f"SKU{num:06d}"
    except Exception as e:
        raise Exception(f"Failed to generate SKU: {str(e)}")

def add_product(product_data, images):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Thêm sản phẩm
    cursor.execute(
        """
        INSERT INTO Product (sku, name, unit, description, cost_price, market_price, min_stock, max_stock, storage_location, supplier_id, category_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            product_data["sku"],
            product_data["name"],
            product_data["unit"],  # Add unit to the query
            product_data["description"],
            product_data["cost_price"],
            product_data["market_price"],
            product_data["min_stock"],
            product_data["max_stock"],
            product_data["storage_location"],
            product_data["supplier_id"],
            product_data["category_id"]
        )
    )
    product_id = cursor.lastrowid
    conn.commit()

    # Xử lý upload hình ảnh
    if images:
        image_dir = Path(f"static/images/product/{product_id}")
        image_dir.mkdir(parents=True, exist_ok=True)
        for i, image in enumerate(images[:5]):  # Giới hạn 5 hình
            file_path = image_dir / f"image_{i+1}.{image.filename.split('.')[-1]}"
            with open(file_path, "wb") as buffer:
                buffer.write(image.file.read())
    conn.commit()
    cursor.close()
    conn.close()
    return product_id
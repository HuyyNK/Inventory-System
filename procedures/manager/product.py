from datetime import datetime
from decimal import Decimal
from database import get_db_connection
from models.product_sql import get_products_sql, add_product_sql, get_max_sku, update_product_sql, get_inbound_details_sql
from pathlib import Path
import os
import shutil

def get_products():
    try:
        products = get_products_sql()
        if not products:
            return []
        # Chuyển đổi datetime thành chuỗi ISO và Decimal thành float
        processed_products = []
        for product in products:
            processed_product = {
                key: value.isoformat() if isinstance(value, datetime) else
                     float(value) if isinstance(value, Decimal) else
                     value
                for key, value in product.items()
            }
            processed_products.append(processed_product)
        return processed_products
    except Exception as e:
        raise

def get_product_by_id(product_id):
    product = get_products_sql(product_id)
    if not product:
        raise Exception(f"Product with ID {product_id} not found")
    # Chuyển đổi Decimal thành float
    processed_product = {
        key: value.isoformat() if isinstance(value, datetime) else
             float(value) if isinstance(value, Decimal) else
             value
        for key, value in product.items()
    }
    return processed_product

def get_inbound_details(product_id):
    details = get_inbound_details_sql(product_id)
    if not details:
        return []
    # Chuyển đổi datetime thành chuỗi ISO và Decimal thành float
    processed_details = []
    for detail in details:
        processed_detail = {
            key: value.isoformat() if isinstance(value, datetime) else
                 float(value) if isinstance(value, Decimal) else
                 value
            for key, value in detail.items()
        }
        processed_details.append(processed_detail)
    return processed_details

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
    try:
        # Thêm sản phẩm
        cursor.execute(
            """
            INSERT INTO Product (sku, name, unit, description, cost_price, market_price, min_stock, max_stock, storage_location, supplier_id, category_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                product_data["sku"],
                product_data["name"],
                product_data["unit"],
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
        return product_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def update_product(product_id, product_data, images):
    try:
        # Cập nhật thông tin sản phẩm trong database
        update_product_sql(product_id, product_data)

        # Xử lý hình ảnh
        image_dir = Path(f"static/images/product/{product_id}")
        if images:  # Chỉ xóa và tạo lại thư mục nếu có ảnh mới
            if image_dir.exists():
                shutil.rmtree(image_dir)
            image_dir.mkdir(parents=True, exist_ok=True)
            for i, image in enumerate(images[:5]):
                file_path = image_dir / f"image_{i+1}.{image.filename.split('.')[-1]}"
                with open(file_path, "wb") as buffer:
                    buffer.write(image.file.read())
        else:  # Nếu không có ảnh mới, giữ nguyên thư mục hiện tại
            if not image_dir.exists():
                image_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise e

def get_product_images(product_id):
    image_dir = Path(f"static/images/product/{product_id}")
    if not image_dir.exists():
        return []
    images = []
    for i in range(1, 6):  # Tối đa 5 hình
        for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            img_path = image_dir / f"image_{i}.{ext}"
            if img_path.exists():
                images.append(f"/static/images/product/{product_id}/image_{i}.{ext}")
                break
    return images
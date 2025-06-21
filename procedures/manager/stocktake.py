from datetime import datetime
from models.stocktake_sql import get_stocktakes, get_inventory, create_stocktake

def get_stocktakes_list():
    try:
        stocktakes = get_stocktakes()
        if not stocktakes:
            return []
        processed_stocktakes = [
            {
                "id": stocktake["id"],
                "date": stocktake["date"].isoformat() if stocktake["date"] else None,
                "status": stocktake["status"],
                "created_by_name": stocktake["created_by_name"],
                "created_by": stocktake["created_by"],
                "total_variance_value": float(stocktake["total_variance_value"]) if stocktake["total_variance_value"] is not None else 0.0
            }
            for stocktake in stocktakes
        ]
        return processed_stocktakes
    except Exception as e:
        raise

def get_inventory_list():
    try:
        inventory = get_inventory()
        if not inventory:
            return []
        processed_inventory = [
            {
                "inventory_id": item["inventory_id"],
                "product_id": item["product_id"],
                "batch_number": item["batch_number"],
                "current_quantity": item["current_quantity"],
                "expiry_date": item["expiry_date"].isoformat() if item["expiry_date"] else None,
                "name": item["name"],
                "sku": item["sku"],
                "cost_price": float(item["cost_price"])
            }
            for item in inventory
        ]
        return processed_inventory
    except Exception as e:
        raise

def create_new_stocktake(date, created_by, status, items):
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        return create_stocktake(date_obj, created_by, status, items)
    except ValueError:
        raise ValueError("Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DD.")
    except Exception as e:
        raise
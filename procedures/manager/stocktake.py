from datetime import datetime, date
from models.stocktake_sql import get_stocktakes, get_inventory, create_stocktake, get_stocktake, update_stocktake

def get_stocktakes_list():
    try:
        stocktakes = get_stocktakes()
        if not stocktakes:
            return []
        processed_stocktakes = [
            {
                key: value.isoformat() if isinstance(value, (datetime, date)) else str(value) if value is not None else None
                for key, value in stocktake.items()
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
                "expiry_date": item["expiry_date"].isoformat() if item["expiry_date"] and isinstance(item["expiry_date"], (datetime, date)) else str(item["expiry_date"]) if item["expiry_date"] else None,
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

def get_stocktake_details(stocktake_id):
    try:
        stocktake = get_stocktake(stocktake_id)
        if not stocktake:
            return None
        inventory = get_inventory()  # Lấy toàn bộ danh sách tồn kho
        existing_details = {d["inventory_id"]: d for d in stocktake.get("details", [])}

        # Gộp dữ liệu hiện có với danh sách tồn kho
        merged_details = []
        for item in inventory:
            detail = existing_details.get(item["inventory_id"], {
                "inventory_id": item["inventory_id"],
                "product_id": item["product_id"],
                "system_quantity": item["current_quantity"],
                "actual_quantity": None,
                "variance": 0,
                "variance_type": "",
                "variance_reason": "",
                "variance_value": 0.0,
                "name": item["name"],
                "sku": item["sku"],
                "batch_number": item["batch_number"],
                "expiry_date": item["expiry_date"],
                "cost_price": item["cost_price"]
            })
            # Chuyển đổi expiry_date nếu là date hoặc datetime
            if isinstance(detail.get("expiry_date"), (datetime, date)):
                detail["expiry_date"] = detail["expiry_date"].isoformat()
            elif detail.get("expiry_date") is None:
                detail["expiry_date"] = None
            if "actual_quantity" in existing_details.get(item["inventory_id"], {}):
                detail["actual_quantity"] = existing_details[item["inventory_id"]]["actual_quantity"]
                detail["variance"] = existing_details[item["inventory_id"]]["variance"]
                detail["variance_type"] = existing_details[item["inventory_id"]]["variance_type"]
                detail["variance_reason"] = existing_details[item["inventory_id"]]["variance_reason"]
                detail["variance_value"] = existing_details[item["inventory_id"]]["variance_value"]
                if "cost_price" not in existing_details[item["inventory_id"]]:
                    detail["cost_price"] = item["cost_price"]
                # Chuyển đổi expiry_date từ existing_details nếu cần
                if isinstance(existing_details[item["inventory_id"]].get("expiry_date"), (datetime, date)):
                    detail["expiry_date"] = existing_details[item["inventory_id"]]["expiry_date"].isoformat()
                elif existing_details[item["inventory_id"]].get("expiry_date") is None:
                    detail["expiry_date"] = None
            merged_details.append(detail)

        return {
            "id": stocktake["id"],
            "date": stocktake["date"].isoformat() if isinstance(stocktake["date"], (datetime, date)) else str(stocktake["date"]) if stocktake["date"] else None,
            "status": stocktake["status"],
            "created_by": stocktake["created_by"],
            "created_by_name": stocktake["created_by_name"],
            "details": merged_details
        }
    except Exception as e:
        raise

def update_stocktake_details(stocktake_id, date, created_by, status, items):
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        print(f"Calling update_stocktake with items: {items}")  # Thêm log
        return update_stocktake(stocktake_id, date_obj, created_by, status, items)
    except ValueError:
        raise ValueError("Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DD.")
    except Exception as e:
        raise
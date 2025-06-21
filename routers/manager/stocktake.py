from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from procedures.auth import get_current_user
from procedures.manager.stocktake import get_stocktakes_list, get_inventory_list, create_new_stocktake
from utils.templates import templates

router = APIRouter(prefix="/manager/stocktake", tags=["manager_stocktake"])

@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_stocktakes_page(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    return templates.TemplateResponse("manager/stocktake/list.html", {"request": request, "user": user})

@router.get("/", response_model=list[dict])
async def list_stocktakes_api(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        stocktakes = get_stocktakes_list()
        return JSONResponse(content=stocktakes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stocktakes: {str(e)}")

@router.get("/add", response_class=HTMLResponse, include_in_schema=False)
async def add_stocktake_page(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    return templates.TemplateResponse("manager/stocktake/add.html", {
        "request": request,
        "user": user,
        "today": "2025-05-28"
    })

@router.get("/inventory", response_model=list[dict])
async def get_inventory_api(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        inventory = get_inventory_list()
        return JSONResponse(content=inventory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inventory: {str(e)}")

@router.post("/add")
async def add_stocktake(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    date = data.get("date")
    created_by = user.get("id")
    status = data.get("status")
    items = data.get("items")

    # Kiểm tra dữ liệu đầu vào
    if not date:
        raise HTTPException(status_code=400, detail="Ngày kiểm kê là bắt buộc")
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="Danh sách chi tiết kiểm kê phải là một mảng")
    if status not in ["Đang kiểm kê", "Đã kiểm kê"]:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

    # Kiểm tra các mục trong items
    for item in items:
        if not isinstance(item.get("inventory_id"), int):
            raise HTTPException(status_code=400, detail="inventory_id phải là số nguyên")
        if not isinstance(item.get("system_quantity"), int):
            raise HTTPException(status_code=400, detail="system_quantity phải là số nguyên")
        if not isinstance(item.get("actual_quantity"), int):
            raise HTTPException(status_code=400, detail="actual_quantity phải là số nguyên")
        if not isinstance(item.get("variance_value"), (int, float)):
            raise HTTPException(status_code=400, detail="variance_value phải là số")

    try:
        result = create_new_stocktake(date, created_by, status, items)
        return JSONResponse(content={"message": "Thêm phiếu kiểm kê thành công!", "id": result["id"]})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Dữ liệu không hợp lệ: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding stocktake: {str(e)}")
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from procedures.auth import get_current_user
from procedures.manager.stocktake import get_stocktakes_list, get_inventory_list, create_new_stocktake, get_stocktake_details, update_stocktake_details
from utils.templates import templates
from datetime import datetime

router = APIRouter(prefix="/employee/stocktake", tags=["employee_stocktake"])

@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_stocktakes_page(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    return templates.TemplateResponse("employee/stocktake/list.html", {"request": request, "user": user})

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
    today = datetime.now().strftime("%Y-%m-%d")
    return templates.TemplateResponse("employee/stocktake/add.html", {
        "request": request,
        "user": user,
        "today": today
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

    if not date:
        raise HTTPException(status_code=400, detail="Ngày kiểm kê là bắt buộc")
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="Danh sách chi tiết kiểm kê phải là một mảng")
    if status not in ["Đang kiểm kê", "Đã kiểm kê"]:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

    for item in items:
        if not isinstance(item.get("inventory_id"), int):
            raise HTTPException(status_code=400, detail="inventory_id phải là số nguyên")
        if not isinstance(item.get("system_quantity"), int):
            raise HTTPException(status_code=400, detail="system_quantity phải là số nguyên")
        if not isinstance(item.get("actual_quantity"), (int, type(None))):
            raise HTTPException(status_code=400, detail="actual_quantity phải là số nguyên hoặc null")
        if item.get("actual_quantity") is not None and item.get("actual_quantity") < 0:
            raise HTTPException(status_code=400, detail="Số lượng thực tế không được âm")
        if item.get("actual_quantity") is not None and item.get("variance") != 0 and not item.get("variance_type"):
            raise HTTPException(status_code=400, detail="Vui lòng chọn loại hao hụt khi có chênh lệch")
        if item.get("actual_quantity") is not None and item.get("variance") != 0 and not item.get("variance_reason"):
            raise HTTPException(status_code=400, detail="Vui lòng nhập lý do chênh lệch")
        if not isinstance(item.get("variance_value"), (int, float)):
            raise HTTPException(status_code=400, detail="variance_value phải là số")

    try:
        result = create_new_stocktake(date, created_by, status, items)
        return JSONResponse(content={"message": "Thêm phiếu kiểm kê thành công!", "id": result["id"]})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Dữ liệu không hợp lệ: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding stocktake: {str(e)}")

@router.get("/view/{stocktake_id}", response_class=HTMLResponse, include_in_schema=False)
async def view_stocktake_page(request: Request, stocktake_id: int, user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        stocktake = get_stocktake_details(stocktake_id)
        if not stocktake:
            raise HTTPException(status_code=404, detail="Phiên kiểm kê không tồn tại")
        can_edit = (user.get("role_id") == 1 or user.get("id") == stocktake.get("created_by")) and stocktake.get("status") == "Đang kiểm kê"
        stocktake = jsonable_encoder(stocktake)
        return templates.TemplateResponse(
            "employee/stocktake/view.html",
            {
                "request": request,
                "user": user,
                "stocktake": stocktake,
                "can_edit": can_edit,
                "today": datetime.now().strftime("%Y-%m-%d")
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stocktake: {str(e)}")

@router.post("/view/{stocktake_id}")
async def update_stocktake(request: Request, stocktake_id: int, user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        stocktake = get_stocktake_details(stocktake_id)
        if not stocktake:
            raise HTTPException(status_code=404, detail="Phiên kiểm kê không tồn tại")
        if not ((user.get("role_id") == 1 or user.get("id") == stocktake.get("created_by")) and stocktake.get("status") == "Đang kiểm kê"):
            raise HTTPException(status_code=403, detail="Không có quyền chỉnh sửa")

        data = await request.json()
        date = data.get("date", stocktake.get("date"))
        status = data.get("status", "Đang kiểm kê")
        items = data.get("items")

        if not isinstance(items, list):
            raise HTTPException(status_code=400, detail="Danh sách chi tiết kiểm kê phải là một mảng")
        if status not in ["Đang kiểm kê", "Đã kiểm kê"]:
            raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

        for item in items:
            if not isinstance(item.get("inventory_id"), int):
                raise HTTPException(status_code=400, detail="inventory_id phải là số nguyên")
            if not isinstance(item.get("actual_quantity"), (int, type(None))):
                raise HTTPException(status_code=400, detail="actual_quantity phải là số nguyên hoặc null")
            if item.get("actual_quantity") is not None and item.get("actual_quantity") < 0:
                raise HTTPException(status_code=400, detail="Số lượng thực tế không được âm")
            if item.get("actual_quantity") is not None and item.get("variance") != 0 and not item.get("variance_type"):
                raise HTTPException(status_code=400, detail="Vui lòng chọn loại hao hụt khi có chênh lệch")
            if item.get("actual_quantity") is not None and item.get("variance") != 0 and not item.get("variance_reason"):
                raise HTTPException(status_code=400, detail="Vui lòng nhập lý do chênh lệch")

        result = update_stocktake_details(stocktake_id, date, user.get("id"), status, items)
        return JSONResponse(content={"message": "Cập nhật phiếu kiểm kê thành công!", "id": stocktake_id})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating stocktake: {str(e)}")
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from procedures.auth import get_current_user
from procedures.manager.supplier import get_suppliers

router = APIRouter(prefix="/employee/supplier", tags=["employee_suppliers"])
templates = Jinja2Templates(directory="templates")

# -----------------------------------------------
# HTML ROUTES
# -----------------------------------------------

@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_suppliers_page(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 2:  # Chỉ cho phép Employee (role_id = 2)
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    return templates.TemplateResponse("employee/supplier/list.html", {"request": request, "user": user})

# -----------------------------------------------
# JSON ROUTES
# -----------------------------------------------

@router.get("/", response_model=list[dict])
async def list_suppliers_api(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 2:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    suppliers = get_suppliers()
    return JSONResponse(content=suppliers)
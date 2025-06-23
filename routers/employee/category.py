from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from procedures.auth import get_current_user
from procedures.manager.category import get_categories

router = APIRouter(prefix="/employee/category", tags=["employee_categories"])
templates = Jinja2Templates(directory="templates")

# -----------------------------------------------
# HTML ROUTES
# -----------------------------------------------

@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_categories_page(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 2:  # Chỉ cho phép Employee (role_id = 2)
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    return templates.TemplateResponse("employee/category/list.html", {"request": request, "user": user})

# -----------------------------------------------
# JSON ROUTES
# -----------------------------------------------

@router.get("/", response_model=list[dict])
async def list_categories_api(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 2:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    categories = get_categories()
    return JSONResponse(content=categories)
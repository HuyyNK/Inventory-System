from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from procedures.auth import get_current_user
from procedures.manager.product import get_products

router = APIRouter(prefix="/employee/product", tags=["employee_products"])
templates = Jinja2Templates(directory="templates")

# -----------------------------------------------
# HTML ROUTES
# -----------------------------------------------
@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_products_page(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 2:  # Chỉ cho phép Employee (role_id = 2)
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    return templates.TemplateResponse("employee/product/list.html", {"request": request, "user": user})

# -----------------------------------------------
# JSON ROUTES
# -----------------------------------------------
@router.get("/", response_model=list[dict])
async def list_products_api(request: Request, user: dict = Depends(get_current_user)):
    try:
        if user.get("role_id") != 2:  
            raise HTTPException(status_code=403, detail="Không có quyền truy cập")
        products = get_products()
        if not products:
            return []
        return JSONResponse(content=products)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")
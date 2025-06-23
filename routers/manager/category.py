from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from procedures.auth import get_current_user
from procedures.manager.category import get_categories, delete_category, add_category, update_category, get_category_by_id

router = APIRouter(prefix="/manager/category", tags=["manager_categories"])
templates = Jinja2Templates(directory="templates")

# -----------------------------------------------
# HTML ROUTES
# Các route này trả về nội dung HTML, được sử dụng để render giao diện người dùng.
# -----------------------------------------------

@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_categories_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("manager/category/list.html", {"request": request, "user": user})

@router.get("/add", response_class=HTMLResponse)
async def add_category_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("manager/category/add.html", {"request": request, "user": user})

@router.get("/update/{category_id}", response_class=HTMLResponse)
async def update_category_page(request: Request, category_id: int, user: dict = Depends(get_current_user)):
    category = get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return templates.TemplateResponse(
        "manager/category/update.html",
        {"request": request, "user": user, "category": category}
    )

@router.post("/add")
async def add_category_form(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    user: dict = Depends(get_current_user)
):
    try:
        add_category(name, description)
        return RedirectResponse(url="/manager/category/list?success=Thêm danh mục thành công", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "manager/category/add.html",
            {"request": request, "user": user, "error": str(e), "value": {"name": name, "description": description}}
        )

# -----------------------------------------------
# JSON ROUTES
# Các route này trả về dữ liệu JSON, được sử dụng cho các yêu cầu AJAX/Fetch từ frontend.
# -----------------------------------------------

@router.get("/", response_model=list[dict])
async def list_categories_api(request: Request, user: dict = Depends(get_current_user)):
    categories = get_categories()
    return JSONResponse(content=categories)

@router.get("/{category_id}", response_model=dict)
async def get_category_api(category_id: int, user: dict = Depends(get_current_user)):
    category = get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/", status_code=201)
async def create_category(request: Request, user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    name = data.get("name")
    description = data.get("description")

    if not name or not isinstance(name, str) or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Name is required and must be a non-empty string")

    category_data = add_category(
        name=name,
        description=description if description else None
    )
    return category_data

@router.put("/{category_id}")
async def update_category_api(category_id: int, request: Request, user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    name = data.get("name")
    description = data.get("description")
    if not name or not isinstance(name, str) or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Name is required and must be a non-empty string")
    if not update_category(
        category_id=category_id,
        name=name,
        description=description if description else None
    ):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category updated"}

@router.delete("/{category_id}")
async def delete_category_api(category_id: int, user: dict = Depends(get_current_user)):
    if not delete_category(category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}
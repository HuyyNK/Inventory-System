from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from procedures.auth import get_current_user
from procedures.manager.product import get_products, get_next_sku, add_product, get_product_by_id, update_product, get_product_images, get_inbound_details
from procedures.manager.category import get_categories_sql
from procedures.manager.supplier import get_suppliers_sql


router = APIRouter(prefix="/manager/product", tags=["manager_products"])
templates = Jinja2Templates(directory="templates")

# -----------------------------------------------
# HTML ROUTES
# Các route này trả về nội dung HTML, được sử dụng để render giao diện người dùng.
# Mục đích: Cung cấp các trang web (list.html, add.html, update.html) để người dùng tương tác.
# Đặt các route tĩnh (như /list, /add) trước route động (như /{product_id}) để tránh xung đột.
# -----------------------------------------------
@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_products_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("manager/product/list.html", {"request": request, "user": user})

@router.get("/add", response_class=HTMLResponse)
async def add_product_page(request: Request, user: dict = Depends(get_current_user)):
    categories = get_categories_sql()
    suppliers = get_suppliers_sql()
    return templates.TemplateResponse("manager/product/add.html", {
        "request": request,
        "user": user,
        "category_options": [{"id": c["id"], "name": c["name"]} for c in categories],
        "supplier_options": [{"id": s["id"], "name": s["name"]} for s in suppliers],
        "storage_options": ['Chilled Storage', 'Ambient Storage', 'Frozen Storage']
    })

@router.get("/update/{product_id}", response_class=HTMLResponse)
async def update_product_page(request: Request, product_id: int, user: dict = Depends(get_current_user)):
    try:
        product = get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        categories = get_categories_sql()
        suppliers = get_suppliers_sql()
        product_images = get_product_images(product_id)
        inbound_details = get_inbound_details(product_id)
        return templates.TemplateResponse("manager/product/update.html", {
            "request": request,
            "user": user,
            "product": product,
            "category_options": [{"id": c["id"], "name": c["name"]} for c in categories],
            "supplier_options": [{"id": s["id"], "name": s["name"]} for s in suppliers],
            "product_images": product_images,
            "inbound_details": inbound_details
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------
# JSON ROUTES
# Các route này trả về dữ liệu JSON, được sử dụng cho các yêu cầu AJAX/Fetch từ frontend.
# Mục đích: Cung cấp dữ liệu động để frontend xử lý (lấy danh sách, thêm, sửa, xóa sản phẩm).
# -----------------------------------------------

@router.get("/", response_model=list[dict])
async def list_products_api(request: Request, user: dict = Depends(get_current_user)):
    try:
        products = get_products()
        if not products:
            return []
        return JSONResponse(content=products)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")
    
@router.get("/next-sku", response_model=dict)
async def get_next_sku_api(user: dict = Depends(get_current_user)):
    try:
        sku = get_next_sku()
        if not sku:
            raise HTTPException(status_code=500, detail="Failed to generate SKU")
        return JSONResponse(content={"sku": sku})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating SKU: {str(e)}")

@router.post("/", status_code=201)
async def create_product(
    request: Request,
    name: str = Form(...),
    category_id: str = Form(...),
    supplier_id: str = Form(...),
    unit: str = Form(None),
    description: str = Form(None),
    cost_price: float = Form(...),
    market_price: float = Form(...),
    min_stock: int = Form(...),
    max_stock: int = Form(...),
    storage_location: str = Form(None),
    sku: str = Form(...),
    images: list[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    try:
        try:
            category_id = int(category_id)
            supplier_id = int(supplier_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Category ID and Supplier ID must be valid integers")

        product_data = {
            "name": name,
            "category_id": category_id,
            "supplier_id": supplier_id,
            "unit": unit,
            "description": description,
            "cost_price": cost_price,
            "market_price": market_price,
            "min_stock": min_stock,
            "max_stock": max_stock,
            "storage_location": storage_location,
            "sku": sku
        }
        product_id = add_product(product_data, images)

        return JSONResponse(content={"id": product_id, "message": "Product added successfully"})
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{product_id}", status_code=200)
async def update_product_api(
    product_id: int,
    request: Request,
    name: str = Form(...),
    category_id: str = Form(...),
    supplier_id: str = Form(...),
    unit: str = Form(None),
    description: str = Form(None),
    cost_price: float = Form(...),
    market_price: float = Form(...),
    min_stock: int = Form(...),
    max_stock: int = Form(...),
    storage_location: str = Form(None),
    images: list[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    try:
        try:
            category_id = int(category_id)
            supplier_id = int(supplier_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Category ID and Supplier ID must be valid integers")

        # Kiểm tra storage_location
        valid_storage_locations = ['Chilled Storage', 'Ambient Storage', 'Frozen Storage']
        if storage_location and storage_location not in valid_storage_locations:
            raise HTTPException(status_code=400, detail="Invalid storage location")

        product_data = {
            "name": name,
            "category_id": category_id,
            "supplier_id": supplier_id,
            "unit": unit,
            "description": description,
            "cost_price": cost_price,
            "market_price": market_price,
            "min_stock": min_stock,
            "max_stock": max_stock,
            "storage_location": storage_location
        }
        update_product(product_id, product_data, images)

        return JSONResponse(content={"id": product_id, "message": "Product updated successfully"})
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
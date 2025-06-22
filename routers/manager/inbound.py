from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from procedures.auth import get_current_user
from procedures.manager.inbound import get_inbounds_list, get_suppliers, get_products, get_inbound_details
from models.inbound_sql import create_inbound
from database import redis_client
from datetime import datetime
from utils.templates import templates

router = APIRouter(prefix="/manager/inbound", tags=["manager_inbound"])

@router.get("/add", response_class=HTMLResponse, include_in_schema=False)
async def add_inbound_page(request: Request, user: dict = Depends(get_current_user)):
    suppliers = get_suppliers()
    products = get_products()
    return templates.TemplateResponse("manager/inbound/add.html", {
        "request": request,
        "user": user,
        "suppliers": suppliers,
        "products": products,
        "today": datetime.now().date().isoformat()
    })

@router.get("/add-product-row", response_class=HTMLResponse, include_in_schema=False)
async def add_product_row(request: Request, index: int, supplier_id: int = None, user: dict = Depends(get_current_user)):
    products = get_products(supplier_id) if supplier_id else get_products()
    return templates.TemplateResponse("manager/inbound/product_row.html", {
        "request": request,
        "index": index,
        "products": products,
        "today": datetime.now().date().isoformat()
    })

@router.get("/products/by-supplier/{supplier_id}", response_model=list[dict])
async def get_products_by_supplier(supplier_id: int, user: dict = Depends(get_current_user)):
    try:
        products = get_products(supplier_id)
        return JSONResponse(content=products)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.get("/products/list", response_model=list[dict])
async def list_products(request: Request, user: dict = Depends(get_current_user)):
    try:
        products = get_products()
        return JSONResponse(content=products)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.post("/add")
async def add_inbound(
    request: Request,
    supplier_id: int = Form(...),
    date: str = Form(...),
    notes: str = Form(None),
    user: dict = Depends(get_current_user)
):
    try:
        created_by = user.get("id")
        date_obj = datetime.now().date()
        form_data = await request.form()
        products = []
        index = 0
        while True:
            product_id_key = f"products[{index}][product_id]"
            unit_price_key = f"products[{index}][unit_price]"
            quantity_key = f"products[{index}][quantity]"
            manufacturing_date_key = f"products[{index}][manufacturing_date]"
            expiry_date_key = f"products[{index}][expiry_date]"
            if product_id_key not in form_data:
                break
            product_id = int(form_data[product_id_key])
            unit_price = float(form_data[unit_price_key])
            quantity = int(form_data[quantity_key])
            manufacturing_date = datetime.strptime(form_data[manufacturing_date_key], "%Y-%m-%d").date()
            expiry_date = datetime.strptime(form_data[expiry_date_key], "%Y-%m-%d").date()
            batch_number = f"LOT{datetime.now().strftime('%Y%m%d')}{index}"
            products.append({
                "product_id": product_id,
                "unit_price": unit_price,
                "quantity": quantity,
                "manufacturing_date": manufacturing_date,
                "expiry_date": expiry_date,
                "batch_number": batch_number
            })
            index += 1

        if not products:
            raise HTTPException(status_code=400, detail="Vui lòng thêm ít nhất một sản phẩm!")

        result = create_inbound(supplier_id, date_obj, created_by, notes, products)
        # Xóa cache sau khi cập nhật
        redis_client.delete("cache:inbound:list")
        redis_client.delete("cache:products")
        for key in redis_client.keys("cache:products:*"):
            redis_client.delete(key)
        redis_client.delete(f"cache:inbound:detail:{result['id']}")
        return JSONResponse(content={"message": "Thêm phiếu nhập thành công!", "id": result["id"]})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Dữ liệu không hợp lệ: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding inbound: {str(e)}")

@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_inbounds_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("manager/inbound/list.html", {"request": request, "user": user})

@router.get("/", response_model=list[dict])
async def list_inbounds_api(request: Request, user: dict = Depends(get_current_user)):
    try:
        inbounds = get_inbounds_list()
        if not inbounds:
            return []
        return JSONResponse(content=inbounds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inbounds: {str(e)}")

@router.get("/detail/{inbound_id}", response_class=HTMLResponse, include_in_schema=False)
async def detail_inbound_page(request: Request, inbound_id: int, user: dict = Depends(get_current_user)):
    try:
        inbound, inbound_details = get_inbound_details(inbound_id)
        if not inbound:
            raise HTTPException(status_code=404, detail="Phiếu nhập không tồn tại")
        return templates.TemplateResponse("manager/inbound/detail.html", {
            "request": request,
            "user": user,
            "inbound": inbound,
            "inbound_details": inbound_details
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inbound details: {str(e)}")
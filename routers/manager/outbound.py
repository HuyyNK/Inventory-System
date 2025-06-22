from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from procedures.auth import get_current_user
from procedures.manager.outbound import get_outbounds_list, get_products_list, create_new_outbound
from models.outbound_sql import get_outbound_by_id
from database import redis_client
from datetime import datetime
from utils.templates import templates

router = APIRouter(prefix="/manager/outbound", tags=["manager_outbound"])

@router.get("/add", response_class=HTMLResponse, include_in_schema=False)
async def add_outbound_page(request: Request, user: dict = Depends(get_current_user)):
    products = get_products_list()
    return templates.TemplateResponse("manager/outbound/add.html", {
        "request": request,
        "user": user,
        "products": products,
        "today": datetime.now().date().isoformat()
    })

@router.get("/add-product-row", response_class=HTMLResponse, include_in_schema=False)
async def add_product_row(request: Request, index: int, user: dict = Depends(get_current_user)):
    products = get_products_list()
    return templates.TemplateResponse("manager/outbound/product_row.html", {
        "request": request,
        "index": index,
        "products": products,
        "today": datetime.now().date().isoformat()
    })

@router.post("/add")
async def add_outbound(
    request: Request,
    customer_name: str = Form(None),
    date: str = Form(...),
    notes: str = Form(None),
    outbound_type: str = Form(...),
    user: dict = Depends(get_current_user)
):
    try:
        created_by = user.get("id")
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        form_data = await request.form()
        products = []
        index = 0
        while True:
            product_id_key = f"products[{index}][product_id]"
            quantity_key = f"products[{index}][quantity]"
            unit_price_key = f"products[{index}][unit_price]"
            if product_id_key not in form_data:
                break
            product_id = form_data[product_id_key]
            if not product_id or not product_id.isdigit():
                raise ValueError(f"ID sản phẩm không hợp lệ tại dòng {index + 1}")
            product_id = int(product_id)
            quantity = int(form_data[quantity_key])
            unit_price = float(form_data[unit_price_key])
            products.append({"product_id": product_id, "quantity": quantity, "unit_price": unit_price})
            index += 1

        if not products:
            raise HTTPException(status_code=400, detail="Vui lòng thêm ít nhất một sản phẩm!")

        valid_outbound_types = ['Bán hàng', 'Chuyển kho', 'Hàng hỏng', 'Hết hạn', 'Khuyến mãi', 'Hoàn trả nhà cung cấp']
        if outbound_type not in valid_outbound_types:
            raise HTTPException(status_code=400, detail="Loại xuất không hợp lệ!")

        result = create_new_outbound(customer_name, date_obj, created_by, notes, outbound_type, products)
        # Xóa cache sau khi thêm
        redis_client.delete("cache:outbound:list")
        redis_client.delete(f"cache:outbound:detail:{result['id']}")
        for product in products:
            redis_client.delete(f"cache:inventory:product:{product['product_id']}")
        return JSONResponse(content={"message": "Thêm phiếu xuất thành công!", "id": result["id"]})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Dữ liệu không hợp lệ: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding outbound: {str(e)}")

@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_outbounds_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("manager/outbound/list.html", {"request": request, "user": user})

@router.get("/", response_model=list[dict])
async def list_outbounds_api(request: Request, user: dict = Depends(get_current_user)):
    try:
        outbounds = get_outbounds_list()
        if not outbounds:
            return []
        return JSONResponse(content=outbounds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching outbounds: {str(e)}")

@router.get("/detail/{outbound_id}", response_class=HTMLResponse, include_in_schema=False)
async def detail_outbound_page(request: Request, outbound_id: int, user: dict = Depends(get_current_user)):
    try:
        result = get_outbound_by_id(outbound_id)  # Lấy dictionary từ get_outbound_by_id
        if not result:
            raise HTTPException(status_code=404, detail="Phiếu xuất không tồn tại")
        outbound = result["outbound"]  # Lấy phần outbound từ dictionary
        outbound_details = result["details"]  # Lấy phần details từ dictionary
        return templates.TemplateResponse("manager/outbound/detail.html", {
            "request": request,
            "user": user,
            "outbound": outbound,
            "outbound_details": outbound_details
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching outbound details: {str(e)}")
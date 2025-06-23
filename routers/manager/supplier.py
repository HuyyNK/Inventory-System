from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from procedures.auth import get_current_user
from procedures.manager.supplier import get_suppliers, delete_supplier, add_supplier, update_supplier, get_supplier_by_id

router = APIRouter(prefix="/manager/supplier", tags=["manager_suppliers"])
templates = Jinja2Templates(directory="templates")

# -----------------------------------------------
# HTML ROUTES
# Các route này trả về nội dung HTML, được sử dụng để render giao diện người dùng.
# Mục đích: Cung cấp các trang web (list.html, add.html, update.html) để người dùng tương tác.
# Đặt các route tĩnh (như /list, /add) trước route động (như /{supplier_id}) để tránh xung đột.
# -----------------------------------------------

@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_suppliers_page(request: Request, user: dict = Depends(get_current_user)):
    """
    Render trang danh sách nhà cung cấp (list.html).
    Truy cập qua URL /manager/suppliers/list.
    Yêu cầu người dùng đăng nhập (get_current_user).
    """
    return templates.TemplateResponse("manager/supplier/list.html", {"request": request, "user": user})

@router.get("/add", response_class=HTMLResponse)
async def add_supplier_page(request: Request, user: dict = Depends(get_current_user)):
    """
    Render trang thêm nhà cung cấp (add.html).
    Truy cập qua URL /manager/suppliers/add.
    Yêu cầu người dùng đăng nhập (get_current_user).
    """
    return templates.TemplateResponse("manager/supplier/add.html", {"request": request, "user": user})

@router.get("/update/{supplier_id}", response_class=HTMLResponse)
async def update_supplier_page(request: Request, supplier_id: int, user: dict = Depends(get_current_user)):
    """
    Render trang sửa nhà cung cấp (update.html).
    Truy cập qua URL /manager/suppliers/update/{supplier_id}.
    Yêu cầu người dùng đăng nhập (get_current_user).
    """
    supplier = get_supplier_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return templates.TemplateResponse(
        "manager/supplier/update.html",
        {"request": request, "user": user, "supplier": supplier}
    )

@router.post("/add")
async def add_supplier_form(
    request: Request,
    name: str = Form(...),
    phone: str = Form(None),
    email: str = Form(None),
    address: str = Form(None),
    user: dict = Depends(get_current_user)
):
    """
    Xử lý form thêm nhà cung cấp (dành cho phương thức POST từ add.html).
    Nhận dữ liệu từ form (không phải JSON), thêm nhà cung cấp và redirect về trang danh sách.
    Nếu có lỗi, render lại add.html với thông báo lỗi.
    """
    try:
        add_supplier(name, phone, email, address)
        return RedirectResponse(url="/manager/supplier/list?success=Thêm nhà cung cấp thành công", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "manager/supplier/add.html",
            {"request": request, "user": user, "error": str(e), "value": {"name": name, "phone": phone, "email": email, "address": address}}
        )

# -----------------------------------------------
# JSON ROUTES
# Các route này trả về dữ liệu JSON, được sử dụng cho các yêu cầu AJAX/Fetch từ frontend.
# Mục đích: Cung cấp dữ liệu động để frontend xử lý (lấy danh sách, thêm, sửa, xóa nhà cung cấp).
# -----------------------------------------------

@router.get("/", response_model=list[dict])
async def list_suppliers_api(request: Request, user: dict = Depends(get_current_user)):
    """
    Lấy danh sách tất cả nhà cung cấp dưới dạng JSON.
    Được gọi bởi JavaScript trong list.html để hiển thị bảng nhà cung cấp.
    """
    suppliers = get_suppliers()
    return JSONResponse(content=suppliers)

@router.get("/{supplier_id}", response_model=dict)
async def get_supplier_api(supplier_id: int, user: dict = Depends(get_current_user)):
    """
    Lấy thông tin chi tiết của một nhà cung cấp dựa trên supplier_id.
    Được gọi bởi JavaScript trong update.html để điền dữ liệu vào form sửa.
    Trả về lỗi 404 nếu không tìm thấy nhà cung cấp.
    """
    supplier = get_supplier_by_id(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@router.post("/", status_code=201)
async def create_supplier(request: Request, user: dict = Depends(get_current_user)):
    """
    Thêm một nhà cung cấp mới thông qua yêu cầu JSON.
    Được gọi bởi JavaScript trong add.html khi gửi form thêm nhà cung cấp.
    Kiểm tra dữ liệu đầu vào (name là bắt buộc) và trả về dữ liệu nhà cung cấp đã thêm.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")

    if not name or not isinstance(name, str) or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Name is required and must be a non-empty string")

    supplier_data = add_supplier(
        name=name,
        phone=phone if phone else None,
        email=email if email else None,
        address=address if address else None
    )
    return supplier_data

@router.put("/{supplier_id}")
async def update_supplier_api(supplier_id: int, request: Request, user: dict = Depends(get_current_user)):
    """
    Cập nhật thông tin nhà cung cấp dựa trên supplier_id thông qua yêu cầu JSON.
    Được gọi bởi JavaScript trong update.html khi gửi form sửa nhà cung cấp.
    Kiểm tra dữ liệu đầu vào (name là bắt buộc) và trả về thông báo thành công.
    Trả về lỗi 404 nếu không tìm thấy nhà cung cấp.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")
    if not name or not isinstance(name, str) or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Name is required and must be a non-empty string")
    if not update_supplier(
        supplier_id=supplier_id,
        name=name,
        phone=phone if phone else None,
        email=email if email else None,
        address=address if address else None
    ):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier updated"}

@router.delete("/{supplier_id}")
async def delete_supplier_api(supplier_id: int, user: dict = Depends(get_current_user)):
    """
    Xóa một nhà cung cấp dựa trên supplier_id.
    Được gọi bởi JavaScript trong list.html khi nhấn nút xóa.
    Trả về thông báo thành công hoặc lỗi 404 nếu không tìm thấy nhà cung cấp.
    """
    if not delete_supplier(supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier deleted"}
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from procedures.auth import get_current_user
from procedures.manager.employee import get_employees_processed, get_roles_processed, add_employee_processed, get_employee_processed, update_employee_processed

router = APIRouter(prefix="/manager/employee", tags=["manager_employee"])
templates = Jinja2Templates(directory="templates")

@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_employees_page(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    return templates.TemplateResponse("manager/employee/list.html", {"request": request, "user": user})

@router.get("/", response_model=list[dict])
async def list_employees_api(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        employees = get_employees_processed()
        return JSONResponse(content=employees)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

@router.get("/add", response_class=HTMLResponse, include_in_schema=False)
async def add_employee_page(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    roles = get_roles_processed()
    return templates.TemplateResponse("manager/employee/add.html", {"request": request, "user": user, "roles": roles})

@router.post("/add")
async def add_employee_api(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        form_data = await request.form()
        employee_data = dict(form_data)
        success = add_employee_processed(employee_data)
        if success:
            return JSONResponse(content={"message": "Thêm nhân viên thành công!"}, status_code=200)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding employee: {str(e)}")

@router.get("/update/{user_id}", response_class=HTMLResponse, include_in_schema=False)
async def update_employee_page(request: Request, user_id: int, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    selected_user = get_employee_processed(user_id) 
    roles = get_roles_processed()
    return templates.TemplateResponse("manager/employee/update.html", {"request": request, "user": user, "selected_user": selected_user, "roles": roles})

@router.post("/update/{user_id}")
async def update_employee_api(user_id: int, request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") != 1:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        form_data = await request.form()
        employee_data = dict(form_data)
        current_employee = get_employee_processed(user_id)
        if not current_employee:
            raise HTTPException(status_code=404, detail="Nhân viên không tồn tại")
        success = update_employee_processed(user_id, employee_data, current_employee)
        if success:
            return JSONResponse(content={"message": "Cập nhật nhân viên thành công!"}, status_code=200)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating employee: {str(e)}")
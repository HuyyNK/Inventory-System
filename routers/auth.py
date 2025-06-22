from fastapi import APIRouter, Form, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from procedures.auth import get_user_by_username, get_current_user
from models.user_sql import get_user_by_id_sql

router = APIRouter(prefix="", tags=["auth"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    # Trả về trang đăng nhập
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = get_user_by_username(username)
    if not user or user["password"] != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    if not user["is_active"]:
        return templates.TemplateResponse("login.html", {"request": request, "error": "User is inactive"})
    # Lưu toàn bộ thông tin người dùng vào session
    request.session["user"] = {
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "phone": user["phone"],
        "email": user["email"],
        "address": user["address"],
        "birthday": user["birthday"],
        "gender": user["gender"],
        "is_active": user["is_active"],
        "role_id": user["role_id"],
        "role_name": user["role_name"]
    }
    return RedirectResponse(url="/manager/dashboard", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@router.get("/auth/me", response_model=dict)
async def get_current_user_details(user: dict = Depends(get_current_user)):
    try:
        # Lấy thông tin chi tiết từ database
        user_details = get_user_by_id_sql(user["id"])
        if not user_details:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông tin người dùng")
        return JSONResponse(content=user_details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user details: {str(e)}")
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from procedures.auth import get_current_user
from models.user_sql import get_role_name
from procedures.manager.user import change_password, get_user_details, update_user

router = APIRouter(prefix="/manager", tags=["manager_profile"])
templates = Jinja2Templates(directory="templates")

@router.get("/profile", response_class=HTMLResponse)
async def user_profile_page(request: Request, user: dict = Depends(get_current_user)):
    user_data = user.copy()
    user_data["role_name"] = get_role_name(user["role_id"])
    return templates.TemplateResponse(
        "/manager/profile.html",
        {"request": request, "user": user_data}
    )
@router.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request, user: dict = Depends(get_current_user)):
    user_data = request.session.get("user", {})
    if not user_data:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "manager/change_password.html",
        {"request": request, "user": user_data}
    )
    
@router.get("/me", response_model=dict)
async def get_current_user_details(user: dict = Depends(get_current_user)):
    return get_user_details(user)

@router.put("/me")
async def update_current_user(request: Request, user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    full_name = data.get("full_name")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")
    birthday = data.get("birthday")
    gender = data.get("gender")

    # Validate required fields
    if not full_name or not isinstance(full_name, str) or len(full_name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Full name is required and must be a non-empty string")
    if email and not isinstance(email, str):
        raise HTTPException(status_code=400, detail="Email must be a string")
    if phone and not isinstance(phone, str):
        raise HTTPException(status_code=400, detail="Phone must be a string")

    # Gọi procedure để cập nhật user
    update_user(
        user_id=user["id"],
        full_name=full_name,
        phone=phone,
        email=email,
        address=address,
        birthday=birthday,
        gender=gender
    )
    
    # Cập nhật session với thông tin mới
    user_data = request.session.get("user", {})
    user_data.update({
        "full_name": full_name,
        "phone": phone if phone else None,
        "email": email if email else None,
        "address": address if address else None,
        "birthday": birthday if birthday else None,  # birthday đã là chuỗi
        "gender": gender if gender else None
    })
    request.session["user"] = user_data

    return {"message": "User updated successfully"}

@router.put("/change-password")
async def change_user_password(request: Request, user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    old_password = data.get("old_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not old_password or not isinstance(old_password, str):
        raise HTTPException(status_code=400, detail="Old password is required and must be a string")
    if not new_password or not isinstance(new_password, str):
        raise HTTPException(status_code=400, detail="New password is required and must be a string")
    if not confirm_password or not isinstance(confirm_password, str):
        raise HTTPException(status_code=400, detail="Confirm password is required and must be a string")
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirm password do not match")

    change_password(
        user_id=user["id"],
        old_password=old_password,
        new_password=new_password
    )

    return {"message": "Password changed successfully"}
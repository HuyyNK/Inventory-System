from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from procedures.auth import get_current_user
from procedures.manager.dashboard import get_kpi_data, get_charts_data, get_warnings_data, get_activities_data
from utils.templates import templates
from datetime import datetime

router = APIRouter(prefix="/manager/dashboard", tags=["manager_dashboard"])

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    today = datetime.now().strftime("%Y-%m-%d")
    return templates.TemplateResponse("manager/dashboard.html", {
        "request": request,
        "user": user,
        "today": today
    })

@router.get("/kpi")
async def get_kpi(user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        data = get_kpi_data()
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        if "database" in str(e).lower():
            raise HTTPException(status_code=503, detail="Database error")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.get("/charts")
async def get_charts(user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        data = get_charts_data()
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        if "database" in str(e).lower():
            raise HTTPException(status_code=503, detail="Database error")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.get("/warnings")
async def get_warnings(user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        data = get_warnings_data()
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        if "database" in str(e).lower():
            raise HTTPException(status_code=503, detail="Database error")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.get("/activities")
async def get_activities(user: dict = Depends(get_current_user)):
    if user.get("role_id") not in [1, 2]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    try:
        data = get_activities_data()
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        if "database" in str(e).lower():
            raise HTTPException(status_code=503, detail="Database error")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
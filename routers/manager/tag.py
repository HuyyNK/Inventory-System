from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from procedures.auth import get_current_user
from procedures.manager.tag import get_tags, get_tag_by_id, add_tag, update_tag, delete_tag

router = APIRouter(prefix="/manager/tag", tags=["manager_tags"])
templates = Jinja2Templates(directory="templates")

# HTML Routes
@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_tags_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("manager/tag/list.html", {"request": request, "user": user})

@router.get("/add", response_class=HTMLResponse)
async def add_tag_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("manager/tag/add.html", {"request": request, "user": user})

@router.get("/update/{tag_id}", response_class=HTMLResponse)
async def update_tag_page(request: Request, tag_id: int, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(
        "manager/tag/update.html",
        {"request": request, "user": user, "tag_id": tag_id, "tag": get_tag_by_id(tag_id)}
    )

# JSON Routes (RESTful API)
@router.get("/", response_model=list[dict])
async def list_tags_api(request: Request, user: dict = Depends(get_current_user)):
    tags = get_tags()
    return JSONResponse(content=tags)

@router.get("/{tag_id}", response_model=dict)
async def get_tag_api(tag_id: int, user: dict = Depends(get_current_user)):
    tag = get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.post("/", status_code=201)
async def create_tag(request: Request, user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    name = data.get("name")
    description = data.get("description")
    storage_location = data.get("storage_location")
    if not name or not isinstance(name, str) or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Name is required and must be a non-empty string")
    tag_data = add_tag(
        name=name,
        description=description if description else None,
        storage_location=storage_location if storage_location else None
    )
    return tag_data

@router.put("/{tag_id}")
async def update_tag_api(tag_id: int, request: Request, user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    name = data.get("name")
    description = data.get("description")
    storage_location = data.get("storage_location")
    if not name or not isinstance(name, str) or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Name is required and must be a non-empty string")
    if not update_tag(
        tag_id=tag_id,
        name=name,
        description=description if description else None,
        storage_location=storage_location if storage_location else None
    ):
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"message": "Tag updated"}

@router.delete("/{tag_id}")
async def delete_tag_api(tag_id: int, user: dict = Depends(get_current_user)):
    if not delete_tag(tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"message": "Tag deleted"}
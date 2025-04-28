from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from routers.auth import router as auth_router
from routers.manager.supplier import router as manager_supplier_router
from routers.manager.tag import router as manager_tag_router
from routers.manager.user import router as manager_user


app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="simple-secret-key")

# Include routers
app.include_router(auth_router)
app.include_router(manager_supplier_router)
app.include_router(manager_tag_router)
app.include_router(manager_user)

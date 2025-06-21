from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from routers.auth import router as auth_router
from routers.manager.supplier import router as manager_supplier_router
from routers.manager.user import router as manager_user
from routers.manager.product import router as manager_product_router
from routers.manager.category import router as manager_category_router
from routers.manager.inbound import router as manager_inbound_router
from routers.manager.outbound import router as manager_outbound_router  
from routers.manager.employee import router as manager_employee_router 
from routers.manager.stocktake import router as manager_stocktake_router
from utils.templates import templates  # Nhập templates chia sẻ

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="simple-secret-key")

# Include routers
app.include_router(auth_router)
app.include_router(manager_supplier_router)
app.include_router(manager_user)
app.include_router(manager_product_router)
app.include_router(manager_category_router)
app.include_router(manager_inbound_router)
app.include_router(manager_outbound_router) 
app.include_router(manager_employee_router)
app.include_router(manager_stocktake_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
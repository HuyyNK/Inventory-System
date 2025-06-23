import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError
from fastapi import Depends, FastAPI, HTTPException
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
from routers.manager.dashboard import router as manager_dashboard_router
from routers.employee.dashboard import router as employee_dashboard_router
from routers.employee.product import router as employee_product_router
from routers.employee.category import router as employee_category_router
from routers.employee.supplier import router as employee_supplier_router
from routers.employee.inbound import router as employee_inbound_router
from routers.employee.outbound import router as employee_outbound_router
from routers.employee.stocktake import router as employee_stocktake_router
from routers.employee.user import router as employee_user_router
from utils.templates import templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key="simple-secret-key-for-testing")

app.include_router(auth_router)
app.include_router(manager_supplier_router)
app.include_router(manager_user)
app.include_router(manager_product_router)
app.include_router(manager_category_router)
app.include_router(manager_inbound_router)
app.include_router(manager_outbound_router)
app.include_router(manager_employee_router)
app.include_router(manager_stocktake_router)
app.include_router(manager_dashboard_router)
app.include_router(employee_dashboard_router)
app.include_router(employee_product_router)
app.include_router(employee_category_router)
app.include_router(employee_supplier_router)
app.include_router(employee_inbound_router)
app.include_router(employee_outbound_router)
app.include_router(employee_stocktake_router)
app.include_router(employee_user_router)


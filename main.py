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
from utils.templates import templates  # Nhập templates chia sẻ

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="simple-secret-key-for-testing")

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
app.include_router(manager_dashboard_router)

# Khởi tạo Redis client (async)
async def get_redis():
    redis_client = redis.Redis(
        host='localhost',  # sửa lại nếu cần dùng 'localhost' hay '127.0.0.1'
        port=6379,
        decode_responses=True
    )
    try:
        print("🔌 Đang kiểm tra kết nối Redis...")
        pong = await redis_client.ping()
        print(f"✅ Phản hồi từ Redis: {pong}")
        yield redis_client
    except RedisConnectionError as e:
        print(f"❌ Lỗi kết nối Redis: {e}")
        raise HTTPException(status_code=503, detail=f"Lỗi kết nối Redis: {str(e)}")
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi không xác định: {str(e)}")
    finally:
        await redis_client.close()

# Endpoint kiểm tra kết nối Redis
@app.get("/redis-test")
async def redis_test(redis=Depends(get_redis)):
    try:
        pong = await redis.ping()
        print(f"📡 Ping Redis trả về: {pong}")
        if pong:  # Thay vì kiểm tra == "PONG"
            info = await redis.info()
            return {
                "message": "Kết nối Redis thành công!",
                "status": "success",
                "redis_response": pong,
                "redis_info": {
                    "connected_clients": info.get("connected_clients", "N/A"),
                    "used_memory": info.get("used_memory_human", "N/A")
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Kết nối Redis thất bại, phản hồi không mong muốn.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý ping Redis: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

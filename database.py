import mysql.connector
from redis_config import get_redis_client

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="ims"
    )
    
redis_client = get_redis_client()
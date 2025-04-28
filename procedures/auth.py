from models.user_sql import get_user_by_username_sql
from fastapi import Depends, HTTPException, Request

def get_user_by_username(username: str):
    return get_user_by_username_sql(username)
        
def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        if request.headers.get('accept') == 'application/json':
            raise HTTPException(status_code=401, detail="Not authenticated")
        raise HTTPException(status_code=401, detail="Not authenticated", headers={"Location": "/login"})
    return user
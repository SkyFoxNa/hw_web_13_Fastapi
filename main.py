import redis.asyncio as redis
import re
from ipaddress import ip_address
from typing import Callable
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.routes import contacts, birthday, auth, users
from src.conf.config import config

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# banned_ips = [
#     ip_address("127.0.0.1"),
# ]
#
#
# @app.middleware("http")
# async def ban_ips(request: Request, call_next: Callable):
#     ip = ip_address(request.client.host)
#     if ip in banned_ips:
#         return JSONResponse(status_code = status.HTTP_403_FORBIDDEN, content = {"detail": "You are banned"})
#     response = await call_next(request)
#     return response

ALLOWED_IPS = [ip_address("127.0.0.1"),]


@app.middleware("http")
async def limit_access_by_ip(request: Request, call_next: Callable):
    ip = ip_address(request.client.host)
    if ip not in ALLOWED_IPS:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Not allowed IP address"})
    response = await call_next(request)
    return response


user_agent_ban_list = [r"Googlebot", r"Python-urllib", r"bot-Yandex"]


@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    print(request.headers.get("Authorization"))
    user_agent = request.headers.get("user-agent")
    print(user_agent)
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "You are banned"},
            )
    response = await call_next(request)
    return response


app.include_router(auth.router, prefix = "/api")
app.include_router(users.router, prefix = "/api")
app.include_router(contacts.router, prefix = "/api")
app.include_router(birthday.router, prefix = "/api")


@app.on_event("startup")
async def startup() :
    r = await redis.Redis(
        host = config.REDIS_DOMAIN,
        port = config.REDIS_PORT,
        db = 0,
        password = config.REDIS_PASSWORD,
    )
    await FastAPILimiter.init(r)


@app.get("/")
def index() :
    return {"message" : "Contacts Application"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)) :
    try :
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None :
            raise HTTPException(status_code = 500, detail = "Database is not configured correctly")
        return {"message" : "Welcome to FastAPI!"}
    except Exception as e :
        print(e)
        raise HTTPException(status_code = 500, detail = "Error connecting to the database")


if __name__ == "__main__" :
    uvicorn.run(
        "main:app", host = "127.0.0.1", port = 8000, reload = True
    )

import string
import random

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi_limiter.depends import RateLimiter
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import users as repositories_users
from src.services.email import send_email, send_email_reset_password, send_message_password, send_random_password
from src.schemas.user import UserSchema, UserResponse, TokenSchema, RequestEmail, ResetPassword
from src.services.auth import auth_service

router = APIRouter(prefix = '/auth', tags = ['auth'])
get_refresh_token = HTTPBearer()


@router.post("/signup", response_model = UserResponse, status_code = status.HTTP_201_CREATED)
async def signup(body: UserSchema, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)) :
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user :
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = "Account already exists!")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model = TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)) :
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None :
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid registration information!")
    if not user.verified :
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Email not verified!")
    if not auth_service.verify_password(body.password, user.password) :
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Incorrect registration information!")

    # Generate JWT token
    access_token = await auth_service.create_access_token(data = {"sub" : user.email})
    refresh_token = await auth_service.create_refresh_token(data = {"sub" : user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token" : access_token, "refresh_token" : refresh_token, "token_type" : "bearer"}


@router.get('/refresh_token', response_model = TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
                        db: AsyncSession = Depends(get_db)) :
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token :
        await repositories_users.update_token(user, None, db)
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid refresh token!")

    access_token = await auth_service.create_access_token(data = {"sub" : email})
    refresh_token = await auth_service.create_refresh_token(data = {"sub" : email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token" : access_token, "refresh_token" : refresh_token, "token_type" : "bearer"}


@router.get('/verified_email/{token}')
async def verified_email(token: str, db: AsyncSession = Depends(get_db)) :
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None :
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Verification error!")
    if user.verified :
        return {"message" : "Your email is already verified!"}
    await repositories_users.verified_email(email, db)
    return {"message" : "Email verified!"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)) :
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.verified :
        return {"message" : "Your email is already confirmed!"}
    if user :
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message" : "Check your email for confirmation."}


@router.post('/send_reset_password')
async def send_reset_password(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                              db: AsyncSession = Depends(get_db)) :
    user = await repositories_users.get_user_by_email(body.email, db)
    print(user)
    if user :
        background_tasks.add_task(send_email_reset_password, user.email, user.username, str(request.base_url))
    return {"message" : "Check your email for confirmation."}


@router.post('/reset_password/',
             response_model = UserResponse,
             dependencies = [Depends(RateLimiter(times = 1, seconds = 20))], )
async def reset_password(body: ResetPassword,
                         background_tasks: BackgroundTasks,
                         request: Request,
                         db: AsyncSession = Depends(get_db),
                         credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token), ) :
    if body.password1 is body.password2 :
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Password doesn't match")
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user :
        password = auth_service.get_password_hash(body.password1)
        new_user = await repositories_users.update_user_password(email, password, db)
        user = await repositories_users.get_user_by_email(user.email, db)
        background_tasks.add_task(send_message_password, user.email, user.username, str(request.base_url))
        return user
    else :
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid registration information!")


@router.get('/reset_password/{token}',
            dependencies = [Depends(RateLimiter(times = 1, seconds = 20))], )
async def reset_password(bt: BackgroundTasks, request: Request,
                         token: str, db: AsyncSession = Depends(get_db),
                         ) :
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None :
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Reset password error!")
    characters = string.ascii_letters + string.digits + string.punctuation
    password1 = ''.join(random.choice(characters) for i in range(8))
    password = auth_service.get_password_hash(password1)
    print(password1)
    new_user = await repositories_users.update_user_password(email, password, db)
    # user = await repositories_users.get_user_by_email(user.email, db)
    bt.add_task(send_random_password, user.email, user.username, str(request.base_url), password1)
    return {"message" : "New password sent by email!"}


# @router.get('/reset_password/{token}',
#             response_model = UserResponse,
#             dependencies = [Depends(RateLimiter(times = 1, seconds = 20))])
# async def reset_password(token: str, db: AsyncSession = Depends(get_db)) :
#     email = await auth_service.get_email_from_token(token)
#     user = await repositories_users.get_user_by_email(email, db)
#     if user is None :
#         raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Reset password error!")
#     # characters = string.ascii_letters + string.digits + string.punctuation
#     # password1 = ''.join(random.choice(characters) for i in range(8))
#     # password = auth_service.get_password_hash(password1)
#     # print(password1)
#     # new_user = await repositories_users.update_user_password(email, password, db)
#     return RedirectResponse(url = f"/api/auth/send_password/{email}")
#
#
# @router.get('/send_password/{email}',
#              dependencies = [Depends(RateLimiter(times = 1, seconds = 20))])
# async def send_password(email: str, request: Request, bt: BackgroundTasks, db: AsyncSession = Depends(get_db)) :
#     user = await repositories_users.get_user_by_email(email, db)
#     if user is None :
#         raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "User not found!")
#     characters = string.ascii_letters + string.digits + string.punctuation
#     password1 = ''.join(random.choice(characters) for i in range(6, 10))
#     password = auth_service.get_password_hash(password1)
#     print(password1)
#     new_user = await repositories_users.update_user_password(email, password, db)
#     bt.add_task(send_random_password, email, user.username, str(request.base_url), password1)
#     return {"message" : "New password sent by email!"}

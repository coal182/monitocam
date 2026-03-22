from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from models.auth import Token, User
from core.security import create_access_token, get_current_user
from core.system_auth import verify_system_user
from config import get_settings


settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), response: Response = None
):
    if not verify_system_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=settings.jwt.expire_minutes),
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt.expire_minutes * 60,
    )

    return Token(access_token=access_token, username=form_data.username)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"message": "Logged out"}


@router.get("/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    return User(username=current_user["username"])

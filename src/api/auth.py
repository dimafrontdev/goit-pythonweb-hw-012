from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    Request,
)
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from src.schemas import (
    UserCreate,
    User,
    RequestEmail,
    Token,
    TokenRefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from src.services.auth import (
    create_access_token,
    Hash,
    get_email_from_token,
    create_refresh_token,
    verify_refresh_token,
    create_password_reset_token,
    get_email_from_reset_token,
)
from src.services.users import UserService
from src.database.db import get_db
from src.services.email import send_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким іменем вже існує",
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )
    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна адреса не підтверджена",
        )
    access_token = await create_access_token(data={"sub": user.username})
    refresh_token = await create_refresh_token(data={"sub": user.username})
    user.refresh_token = refresh_token
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh-token", response_model=Token)
async def new_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    user = await verify_refresh_token(request.refresh_token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    new_access_token = await create_access_token(data={"sub": user.username})
    user.refresh_token = request.refresh_token
    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": request.refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ваша електронна пошта вже підтверджена",
        )
    await user_service.confirmed_email(email)
    return {"message": "Електронну пошту підтверджено"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Такого користувача не існує",
        )
    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Перевірте свою електронну пошту для підтвердження"}


@router.post("/request_password_reset")
async def request_password_reset(
    body: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Користувача з таким email не знайдено",
        )

    # Create reset token
    token = create_password_reset_token(user.email, expires_hours=1)
    # Send email with the reset link
    background_tasks.add_task(
        send_password_reset_email, user.email, request.base_url, token
    )
    return {"message": "Посилання для скидання пароля відправлено на ваш email."}


@router.post("/confirm_password_reset")
async def confirm_password_reset(
    body: PasswordResetConfirm, db: Session = Depends(get_db)
):
    email = await get_email_from_reset_token(body.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невірний або прострочений токен",
        )
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Користувач не знайдений"
        )

    hashed_password = Hash().get_password_hash(body.new_password)
    await user_service.update_password(email, hashed_password)
    return {"message": "Пароль успішно змінено"}

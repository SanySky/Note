from typing import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db() -> Generator[Session, None, None]:
    """Создает новую сессию базы данных.

       Возвращает:
           Generator[Session]: Генератор сессии базы данных.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db),
                     token: str = Depends(oauth2_scheme)) -> User:
    """Извлекает текущего пользователя из базы данных на основе предоставленного токена.

    Эта функция декодирует JWT-токен, проверяет его на действительность и извлекает пользователя
    из базы данных, основываясь на имени пользователя, указанном в токене.

    Аргументы:
        db (Session, optional): Сессия базы данных. По умолчанию результат функции `get_db`.
        token (str, optional): Токен для аутентификации пользователя. По умолчанию результат функции `oauth2_scheme`.

    Исключения:
        HTTPException: Выбрасывается с кодом 401, если не удалось проверить учетные данные,
                       если токен недействителен или если пользователь не найден в базе данных.

    Возвращает:
        User: Объект пользователя, если токен действителен и пользователь найден.

    Примечание:
        Убедитесь, что токен передан в заголовке `Authorization` в формате `Bearer <token>`.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

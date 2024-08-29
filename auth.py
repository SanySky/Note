from typing import Generator, Optional, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db() -> Generator[Session, None, None]:
    """
        Создает зависимость для работы с базой данных, возвращая объект сессии SQLAlchemy.

        Этот генератор создает новую сессию базы данных и гарантирует, что она будет закрыта
        после завершения работы с ней.

        Yields:
            Session: Объект сессии базы данных.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
       Проверяет, соответствует ли введенный пароль хешированному паролю.

       Args:
           plain_password (str): Введенный пользователем пароль.
           hashed_password (str): Хешированный пароль.

       Returns:
           bool: True, если пароли совпадают, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db: Session, username: str) -> Optional[User]:
    """
        Получает пользователя по имени пользователя из базы данных.

        Args:
            db (Session): Сессия базы данных.
            username (str): Имя пользователя для поиска.

        Returns:
            Optional[User]: Объект пользователя, если найден, иначе None.
    """
    return db.query(User).filter(User.username == username).first()


def create_access_token(data: Dict[str, str],
                        expires_delta: Optional[timedelta] = None) -> str:
    """
        Создает JWT токен для доступа с заданными данными и временем истечения.

        Args:
            data (Dict[str, str]): Данные, которые будут закодированы в токене.
            expires_delta (Optional[timedelta]): Время истечения токена. Если не указано, токен истекает через 15 минут.

        Returns:
            str: Закодированный JWT токен.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme),
                           db: Session = Depends(get_db)) -> User:
    """
        Получает текущего пользователя на основе предоставленного токена.

        Args:
            token (str): JWT токен для аутентификации.
            db (Session): Сессия базы данных.

        Raises:
            HTTPException: Если токен недействителен или пользователь не найден.

        Returns:
            User: Объект текущего пользователя.
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
        token_data = username
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data)
    if user is None:
        raise credentials_exception
    return user

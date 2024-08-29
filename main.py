from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import bcrypt
import jwt
from datetime import datetime, timedelta

from auth import get_current_user, get_db, SECRET_KEY, ALGORITHM
from models import User, Note, NoteCreate, NoteResponse, UserCreate, UserResponse

app = FastAPI()


def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None) -> str:
    """
    Создание токена для пользователя.

    :param data: Словарь с данными, которые будут закодированы в токене.
    :param expires_delta: Время жизни токена. Это значение является объектом
                          timedelta, который определяет, как долго токен будет действительным.
                          Если не указано, токен будет действителен в течение 15 минут.
    :return: Закодированный JWT токен, который можно использовать для аутентификации
             пользователя в последующих запросах.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def check_user_exists(db: Session, username: str) -> Optional[User]:
    """
        Проверяет, существует ли пользователь с заданным именем в базе данных.

        :param db: Объект сессии базы данных, используемый для выполнения запросов.
        :param username: Имя пользователя, которое нужно проверить.

        :return: Объект User, если пользователь с указанным именем существует; иначе None.
    """
    return db.query(User).filter(User.username == username).first()


@app.post("/register/", response_model=UserResponse)
async def register(
    user: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """
       Регистрация нового пользователя.

       :param user: Объект UserCreate, содержащий имя пользователя и пароль.
       :param db: Объект сессии базы данных, используемый для выполнения запросов.

       :raises HTTPException: Если пользователь с таким именем уже существует.

       :return: Объект UserResponse, содержащий имя зарегистрированного пользователя.
    """
    existing_user = await check_user_exists(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует")

    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'),
                                    bcrypt.gensalt())
    db_user = User(username=user.username,
                   hashed_password=hashed_password.decode('utf-8'))

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse(username=db_user.username)


@app.post("/login/")
async def login(user: UserCreate, db: Session = Depends(get_db)) -> dict:
    """
        Выполняет аутентификацию пользователя и возвращает токен доступа.

        :param user: Объект UserCreate, содержащий имя пользователя и пароль.
        :param db: Объект сессии базы данных, используемый для выполнения запросов.

        :raises HTTPException: Если учетные данные неверны.

        :return: Словарь с токеном доступа и типом токена.
    """
    db_user = await check_user_exists(db, user.username)

    if db_user is None or not bcrypt.checkpw(
            user.password.encode('utf-8'),
            db_user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Неверные учетные данные")

    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}


async def check_spelling(content: str) -> List[dict]:
    """
        Проверяет орфографию текста, отправляя запрос к внешнему сервису Яндекс Спеллер

        :param content: Текст, который нужно проверить на орфографические ошибки.

        :return: Список ошибок, найденных в тексте. Если ошибок нет, возвращается пустой список.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://speller.yandex.net/services/spellservice.json/checkText",
            data={"text": content})
    return response.json()


@app.post("/notes/", response_model=NoteResponse)
async def create_note(note: NoteCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) \
        -> NoteResponse:
    """
        Создает новую заметку для текущего пользователя.

        :param note: Объект NoteCreate, содержащий текст заметки.
        :param current_user: Объект User, представляющий текущего аутентифицированного пользователя.
        :param db: Объект сессии базы данных, используемый для выполнения запросов.

        :raises HTTPException: Если в тексте заметки найдены орфографические ошибки.

        :return: Объект NoteResponse, представляющий созданную заметку.
    """
    errors = await check_spelling(note.content)
    if errors:
        raise HTTPException(
            status_code=400,
            detail=
            "В тексте заметки были найдены орфографические ошибки, и заметка не будет создана!"
        )

    db_note = Note(content=note.content, user_id=current_user.id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    return NoteResponse(id=db_note.id,
                        user_id=current_user.id,
                        content=db_note.content)


@app.get("/notes/", response_model=List[NoteResponse])
async def read_notes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) \
        -> List[NoteResponse]:
    """
        Получает все заметки текущего пользователя.

        :param current_user: Объект User, представляющий текущего аутентифицированного пользователя.
        :param db: Объект сессии базы данных, используемый для выполнения запросов.

        :return: Список объектов NoteResponse, представляющих заметки пользователя.
    """
    notes = db.query(Note).filter(Note.user_id == current_user.id).all()
    return [
        NoteResponse(id=note.id, user_id=note.user_id, content=note.content)
        for note in notes
    ]

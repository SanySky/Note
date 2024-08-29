import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()

existing_user = session.query(User).filter_by(username="testuser").first()
if existing_user is None:
    hashed_password = bcrypt.hashpw("testpassword".encode('utf-8'),
                                    bcrypt.gensalt())

    new_user = User(username="testuser",
                    hashed_password=hashed_password.decode('utf-8'))
    session.add(new_user)
    session.commit()
    print("Пользователь успешно добавлен.")
else:
    print("Пользователь с таким именем уже существует.")

session.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://yogsamiti_user:mb3li9c0AUaeZQXdmwDaUKoTSjw2KBFE@dpg-d6rqp9ggjchc73bf371g-a/yogsamiti"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

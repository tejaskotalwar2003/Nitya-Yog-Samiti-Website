from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL")  # 🔥 get from Render env

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}  # 🔥 VERY IMPORTANT
)

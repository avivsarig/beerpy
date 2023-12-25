from backend import settings
import sys

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker, declarative_base


def init_db():
    db_name = settings.DATABASE
    db_host = settings.PGHOST
    db_port = settings.PORT
    db_user = settings.DB_USER
    db_password = settings.PASSWORD

    SQLALCHEMY_DATABASE_URL = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    try:
        connection = engine.connect()
        print("🔗 Database connection established")
    except exc.OperationalError:
        print(
            "❗ Could not connect to the database. Please check your database settings and connection."
        )
        sys.exit(1)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    return engine, SessionLocal, Base, get_db


engine, SessionLocal, Base, get_db = init_db()

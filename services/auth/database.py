from sqlalchemy import create_engine, Column, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./auth.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)


Base.metadata.create_all(bind=engine)

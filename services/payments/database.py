from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./payments.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String, primary_key=True)
    from_account = Column(String)
    to_account = Column(String)
    amount = Column(Float)
    currency = Column(String)
    status = Column(String)
    created_at = Column(DateTime)


Base.metadata.create_all(bind=engine)
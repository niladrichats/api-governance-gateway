from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./payments.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
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


class RejectedPayment(Base):
    __tablename__ = "rejected_payments"

    id = Column(String, primary_key=True)
    payment_id = Column(String)
    from_account = Column(String)
    to_account = Column(String)
    amount = Column(Float)
    currency = Column(String)
    rejection_reason = Column(String)
    fraud_risk_level = Column(String)
    fraud_confidence = Column(Float)
    fraud_reasoning = Column(String)
    rejected_at = Column(DateTime)


Base.metadata.create_all(bind=engine)
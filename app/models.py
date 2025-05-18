from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    reward_points = Column(Integer, default=0)
    bills = relationship("Bill", back_populates="owner")

class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    biller_name = Column(String, index=True)
    bill_type = Column(String)  # Phone, Electricity, Credit Card
    amount = Column(Float)
    due_date = Column(DateTime)
    reminder_frequency = Column(Integer)  # Days
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="bills")

class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    points_required = Column(Integer)
    is_active = Column(Boolean, default=True)
    claims = relationship("RewardClaim", back_populates="reward")

class RewardClaim(Base):
    __tablename__ = "reward_claims"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    reward_id = Column(Integer, ForeignKey("rewards.id"))
    claimed_at = Column(DateTime, default=datetime.utcnow)
    points_used = Column(Integer)
    is_used = Column(Boolean, default=False)
    user = relationship("User", backref="reward_claims")
    reward = relationship("Reward", back_populates="claims") 
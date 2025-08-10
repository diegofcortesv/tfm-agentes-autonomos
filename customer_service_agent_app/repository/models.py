# customer_service_agent_app/repository/models.py
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, TIMESTAMP, JSON, Boolean
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CustomerProfile(Base):
    __tablename__ = 'customer_profiles'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    tier = Column(String(20), default='Basic')
    # ... y así con el resto de las columnas y tablas ...
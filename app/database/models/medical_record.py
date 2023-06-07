import json
from app.database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    id = Column(Integer, primary_key=True, index=True)
    user = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(String)
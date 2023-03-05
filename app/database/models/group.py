
from app.database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship

class Group(Base) :
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    confidant = relationship("Confidant")


class Confidant(Base) :
    __tablename__ = "confidants"
    id = Column(Integer, primary_key=True, index=True)
    user = Column(Integer, ForeignKey("users.id"))
    group = Column(Integer, ForeignKey("groups.id"))
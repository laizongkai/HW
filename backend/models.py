from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from database import Base

class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key = True, index = True)
    username = Column(String, index = True)
    email = Column(String, index = True)
    register_date = Column(Date, index = True)
    
class ConfirmUsers(Base):
    __tablename__ = "confirm_users"
    id = Column(Integer, primary_key = True, index = True)
    email = Column(String, index = True)
    hash_password = Column(String, index = True)
    
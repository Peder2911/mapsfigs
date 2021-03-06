
import os

from sqlalchemy import Column,String,Integer,ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event

eng = create_engine(os.getenv("DB_URI"))
sm = sessionmaker(bind=eng)
Base = declarative_base(bind=eng)

def connect():
    return eng.connect()

def get_session():
    return sm()

class Variable(Base):
    """
    A variable, associating values with mappings and a description
    """
    __tablename__ = "variables"
    id = Column(Integer,primary_key=True)
    name = Column(String,unique=True)
    description = Column(String)
    mappings = relationship("Mapping",back_populates="variable")
    def __repr__(self):
        print(f"{self.name}")

class Mapping(Base):
    """
    Integer -> String mapping for descriptive values
    Used for Domain -> Range when making plots.
    """
    __tablename__ = "mappings"
    id = Column(Integer,primary_key=True)
    variable_id = Column(Integer,ForeignKey("variables.id"))
    variable = relationship("Variable",back_populates="mappings")
    key = Column(Integer)
    value = Column(String)
    def __repr__(self):
        print(f"Mapping 4 {self.variable.name}")


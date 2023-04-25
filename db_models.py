from sqlalchemy import Column, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import Integer, Text, String, JSON, Date

Base = declarative_base()

class Model(Base):
    __tablename__ = "model"

    id = Column(Integer, primary_key=True, autoincrement="auto")
    uid = Column(String(128), unique=True, nullable=False)
    model_metadata = Column(JSON, nullable=False)
    first_seen = Column(Date, nullable=False)
    last_seen = Column(Date, nullable=False)
    operations = relationship("Operation", back_populates="model")

class Operation(Base):
    __tablename__ = "operation"

    id = Column(Integer, primary_key=True, autoincrement="auto")
    name = Column(String(128), nullable=False)
    operation_metadata = Column(JSON, nullable=False)
    first_seen = Column(Date, nullable=False)
    last_seen = Column(Date, nullable=False)
    download_locations = relationship("DownloadLocation", back_populates="operation")

    model_id = Column(Integer, ForeignKey("model.id"), nullable=False)
    model = relationship("Model", back_populates="operations")

class DownloadLocation(Base):
    __tablename__ = "downloadlocation"

    id = Column(Integer, primary_key=True, autoincrement="auto")
    url = Column(String(255), nullable=False)
    
    operation_id = Column(Integer, ForeignKey("operation.id"), nullable=False)
    operation = relationship("Operation", back_populates="download_locations")


engine = create_engine("sqlite:///models.db")
Base.metadata.create_all(engine)
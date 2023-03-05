from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.env import config

SQLALCHEMY_DATABASE_URL = "postgresql://{}:{}@{}/{}".format(config['DB_USER'],config['DB_PASSWORD'],config['DB_HOST'],config['DB_NAME'])
#SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db".format()


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
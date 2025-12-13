from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import config

Base = declarative_base()

engine = create_engine(config.database.url, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

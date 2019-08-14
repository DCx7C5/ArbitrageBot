from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

URI = 'mysql://backend:password@localhost:3306/arbitrage'


def start() -> scoped_session:
    engine = create_engine(URI)
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


BASE = declarative_base()
SESSION = start()

CONNECTION = create_engine(URI)

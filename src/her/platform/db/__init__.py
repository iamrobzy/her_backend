from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..settings import settings

engine = create_engine(settings.database_url, future=True)
Session = sessionmaker(engine, expire_on_commit=False)

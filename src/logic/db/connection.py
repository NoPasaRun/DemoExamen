from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import db_settings


engine = create_engine(db_settings.url, echo=db_settings.echo)
Session = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def create_session(commit: bool = True):
    session = Session()
    try:
        yield session
        if commit:
            session.commit()
    except Exception as err:
        print(f"Error: {err}; Rollback!")
        session.rollback()
    finally:
        session.close()

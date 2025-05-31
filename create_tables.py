from sqlalchemy import create_engine
from app.models.models import Base
from app.core.database import SQLALCHEMY_DATABASE_URL

def create_tables():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables() 
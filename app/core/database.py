from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Cooper@localhost:5432/kplan"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def recreate_tables():
    logging.info("Starting database recreation...")
    try:
        # Drop schema and recreate it
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            conn.commit()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables recreated successfully")
    except Exception as e:
        logging.error(f"Error recreating database: {str(e)}")
        raise

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
from app.core.database import Base, engine
from app.models.models import User, Project, FileUpload, MappingTemplate, ProcessingJob

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!") 
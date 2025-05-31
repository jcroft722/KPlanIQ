from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Cooper@localhost:5432/kplan"

# Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create declarative base
Base = declarative_base()

# Define models
class EmployeeData(Base):
    __tablename__ = "employee_data"

    id = Column(Integer, primary_key=True, index=True)
    ssn = Column(String, unique=True, index=True)
    eeid = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    dob = Column(Date)
    doh = Column(Date)  # Date of Hire
    dot = Column(Date)  # Date of Termination
    hours_worked = Column(Float)
    ownership_percentage = Column(Float)
    is_officer = Column(Boolean)
    prior_year_compensation = Column(Float)
    employee_deferrals = Column(Float)
    employer_match = Column(Float)
    employer_profit_sharing = Column(Float)
    employer_sh_contribution = Column(Float)

class ComplianceTest(Base):
    __tablename__ = "compliance_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String)
    status = Column(String)  # passed, failed, in_progress
    run_date = Column(Date)
    details = Column(String)  # JSON string for test details

class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    status = Column(String)  # uploaded, processed, failed
    uploaded_at = Column(Date)
    rows = Column(Integer)
    columns = Column(Integer)
    headers = Column(String)  # JSON string for headers

def main():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    main() 
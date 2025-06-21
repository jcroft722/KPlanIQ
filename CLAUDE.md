# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KPlan is a full-stack web application for 401(k) plan data management and compliance testing. The system processes employee census data files, validates them, and performs compliance testing. It consists of a React TypeScript frontend, FastAPI Python backend, and PostgreSQL database.

## Commands

### Backend Development

**Start Backend Server:**
```bash
cd backend
.\venv\Scripts\Activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Database Operations:**
```bash
cd backend
.\venv\Scripts\Activate
python create_db.py  # Initialize database tables
```

**Run Backend Tests:**
```bash
cd backend
.\venv\Scripts\Activate
python test_api.py  # Basic API testing
python test_db.py   # Database connection testing
```

**Database Migrations:**
```bash
cd backend
.\venv\Scripts\Activate
alembic upgrade head  # Apply migrations
alembic revision --autogenerate -m "description"  # Create new migration
```

### Frontend Development

**Start Frontend Server:**
```bash
cd frontend
npm start  # Runs on http://localhost:3000
```

**Build Frontend:**
```bash
cd frontend
npm run build
```

**Run Frontend Tests:**
```bash
cd frontend
npm test
```

## Architecture

### Backend Structure (`backend/`)
- **`main.py`**: FastAPI application entry point with all API endpoints
- **`app/models/models.py`**: SQLAlchemy database models for all entities
- **`app/core/database.py`**: Database connection and session management
- **`app/services/`**: Business logic services (validation_engine.py, fix_engine.py)
- **`app/routers/`**: Modular API route handlers (fix_issue_routes.py)
- **`alembic/`**: Database migration files
- **`uploads/`**: File storage directory for uploaded CSV/Excel files

### Frontend Structure (`frontend/src/`)
- **`components/`**: React components organized by feature
  - `FileUpload/`: File upload interface
  - `ColumnMapper.tsx`: Column mapping interface  
  - `ValidationResults.tsx`: Data validation results display
  - `FixIssues/`: Issue resolution interface
  - `ComplianceTestingWorkflow.tsx`: Compliance testing workflow
- **`services/api.ts`**: API communication layer using axios
- **`types/`**: TypeScript type definitions

### Database Models
Key entities and their relationships:
- **FileUpload**: Stores file metadata and processing status
- **RawEmployeeData**: Raw uploaded data as JSON
- **EmployeeData**: Processed/mapped employee records
- **ColumnMapping**: Maps source columns to standard schema
- **ValidationResult**: Data quality issues found
- **ValidationRun**: Validation execution metadata
- **DataQualityScore**: Overall data quality metrics
- **ComplianceTestRun**: Compliance test execution records

## Data Processing Workflow

1. **File Upload** → FileUpload record created, data stored in RawEmployeeData
2. **Column Mapping** → Automatic suggestions + manual mapping stored in ColumnMapping
3. **Data Processing** → Raw data transformed to EmployeeData using mappings
4. **Validation** → DataValidationEngine runs comprehensive checks
5. **Issue Resolution** → Auto-fixes applied or manual corrections made
6. **Compliance Testing** → Final compliance tests executed

## Key Services

### DataValidationEngine (`backend/app/services/validation_engine.py`)
Comprehensive data validation system that:
- Validates required fields and data formats
- Performs cross-field logic checks
- Detects anomalies and inconsistencies
- Calculates data quality scores
- Provides auto-fix suggestions

### Column Mapping System
Automatic column mapping with fuzzy matching:
- Standard 401(k) schema defined in `STANDARD_COLUMNS`
- Variation patterns in `COLUMN_VARIATIONS`
- Confidence scoring for auto-suggestions

## API Endpoints

### File Management
- `POST /api/files/upload` - Upload CSV/Excel files
- `GET /api/files/uploads` - List uploaded files
- `GET /api/files/{id}` - Get file details
- `POST /api/files/{id}/process` - Process uploaded file
- `PUT /api/files/{id}/mappings` - Update column mappings

### Data Validation
- `POST /api/files/{id}/validate` - Run comprehensive validation
- `GET /api/files/{id}/validation-results` - Get validation results
- `POST /api/files/{id}/auto-fix` - Apply automatic fixes
- `GET /api/files/{id}/quality-score` - Get data quality score

### Issue Resolution
- `POST /api/fix-issues/session/start` - Start fix session
- `POST /api/fix-issues/session/{id}/apply-fix` - Apply specific fix
- `GET /api/fix-issues/session/{id}/issues` - Get session issues

### Compliance Testing
- `POST /api/files/{id}/compliance-test` - Run compliance tests
- `GET /api/compliance/results` - Get recent test results
- `GET /api/compliance/history` - Get test history

## Development Environment

- **Backend**: Python 3.8+, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, TypeScript, Axios
- **Database**: PostgreSQL with Alembic migrations
- **File Storage**: Local filesystem (uploads/ directory)

## Database Configuration

Database connection configured via environment variable `DATABASE_URL` in backend. Default setup expects PostgreSQL database named `kplan`.

## Testing

- Backend API testing via `test_api.py` (manual HTTP requests)
- Database connectivity testing via `test_db.py`
- Frontend uses React Testing Library (configured in package.json)

## File Processing

Supports CSV and Excel formats. Files are:
1. Stored in `backend/uploads/` with timestamp prefixes
2. Raw data preserved in `RawEmployeeData` table
3. Processed data stored in `EmployeeData` after column mapping
4. Validation applied to detect and fix data quality issues
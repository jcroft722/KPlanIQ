# KPlan Project Setup Guide

This project consists of a React frontend and FastAPI backend with PostgreSQL database.

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- PostgreSQL database
- pip (Python package manager)
- npm (Node package manager)

## One-Time Setup Activities

### 1. Database Setup
1. Install PostgreSQL if you haven't already
2. Create a new database named `kplan`
3. Update the database connection string in `backend/app/core/database.py` if needed

### 2. Backend Initial Setup

## Backend Setup (Windows/PowerShell)

1. **Create and activate the virtual environment:**
   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
   - If you encounter `ModuleNotFoundError: No module named 'psycopg2'`, ensure you are in the correct virtual environment and run:
   ```powershell
   pip install psycopg2-binary
   ```
3. **Run the backend server:**
   ```powershell
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### 3. Frontend Initial Setup
```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## Daily/Regular Activities

### 1. Start the Backend Server
```powershell
# Navigate to backend directory
cd backend

# Activate virtual environment (if not already activated)
.\venv\Scripts\Activate

# Start the server using uvicorn
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
The backend server will run on http://localhost:8000
- API documentation is available at http://localhost:8000/docs
- Health check endpoint is available at http://localhost:8000/health

### 2. Start the Frontend Development Server
```powershell
# Navigate to frontend directory
cd frontend

# Start the development server
npm start
```
The frontend will run on http://localhost:3000

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Verify database credentials in `backend/app/core/database.py`
   - Make sure the database `kplan` exists

2. **ModuleNotFoundError: No module named 'psycopg2'**
   - Run: `pip install psycopg2-binary`

3. **PowerShell Command Issues**
   - Use semicolon (;) instead of && for command chaining
   - Run commands separately if needed

4. **Port Already in Use**
   - Ensure no other services are running on ports 3000 or 8000
   - Kill the process using the port or change the port in the configuration

5. **Backend Server Not Starting**
   - Make sure you're using the correct command: `python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
   - Check that PostgreSQL is running
   - Verify all dependencies are installed

6. **Database Table Errors**
   - If you see "relation does not exist" errors, run the database initialization script:
     ```powershell
     cd backend
     .\venv\Scripts\Activate
     python create_db.py
     ```

## Development

- Backend API documentation is available at http://localhost:8000/docs when the server is running
- Frontend development server includes hot-reloading
- Database migrations are handled using Alembic

## Project Structure

```
kplan-project/
├── backend/
│   ├── app/
│   ├── main.py
│   ├── requirements.txt
│   └── create_db.py
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
└── SETUP.md
```

## Quick Start (After Initial Setup)

Once you've completed the one-time setup activities, you only need to:

1. Start PostgreSQL (if not running)
2. Start the backend:
   ```powershell
   cd backend
   .\venv\Scripts\Activate
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
3. Start the frontend:
   ```powershell
   cd frontend
   npm start
   ```

## Troubleshooting
- If you see errors about missing modules, double-check that your virtual environment is activated (`(venv)` should appear in your prompt).
- If you have multiple project folders or virtual environments, make sure you are using the one inside `kplan-project/backend/venv`.
- If you still see `ModuleNotFoundError: No module named 'psycopg2'`, try deactivating and reactivating the virtual environment, then reinstalling dependencies. 
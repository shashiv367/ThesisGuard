# ThesisGuard Engine

Backend API for the AI-Based Semantic Plagiarism Detection Engine.

## Local Setup Steps

To run the application locally, you must first set up a PostgreSQL database with the `pgvector` extension.

### 1. Install PostgreSQL
Install PostgreSQL (version 16 recommended) on your machine. Keep note of the password for the default `postgres` superuser.

### 2. Install pgvector
Install the `pgvector` extension for your PostgreSQL installation. (See the project documentation for specific instructions for Windows, macOS, or Linux).

### 3. Create the Database and User
Open `psql` or a SQL client and run:
```sql
CREATE DATABASE thesisguard;
CREATE USER thesisguard_user WITH PASSWORD 'choose_a_password';
GRANT ALL PRIVILEGES ON DATABASE thesisguard TO thesisguard_user;
```

Connect to the database (`\c thesisguard` or `psql -d thesisguard`) and enable the extension:
```sql
CREATE EXTENSION vector;
```

### 4. Create a .env File
Create a `.env` file in the root of the project with your connection details:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=thesisguard
DB_USER=thesisguard_user
DB_PASSWORD=choose_a_password
```

*See the full project documentation (Section 6.1.1) for a comprehensive walkthrough of the DB setup.*

### 5. Running the API
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

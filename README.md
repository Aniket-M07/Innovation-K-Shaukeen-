# Campus Search Engine

A Flask-based campus document search app with authentication, role-based upload access, and keyword/prefix/filename search.

## Features

- User signup/login with session-based auth
- Roles: `Student` and `Admin`
- Admin-only document upload (`.pdf`, `.txt`)
- Search modes:
  - Keyword search
  - Prefix search
  - Filename search
- Autocomplete suggestions
- File serving for uploaded documents
- SQLite user storage

## Project Structure

```text
backend/
  app.py
  database.py
  search_engine.py
  datastructure/
  ingestion/
  uploads/
frontend/
  templates/
  static/
```

## Requirements

- Python 3.9+
- pip

## Setup

From the project root:

```bash
python -m venv .venv
```

### Windows (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
pip install flask pypdf2
```

### macOS/Linux

```bash
source .venv/bin/activate
pip install flask pypdf2
```

## Run

From the project root:

```bash
python backend/app.py
```

The app runs at:

- `http://127.0.0.1:5000`
- `http://localhost:5000`

## Authentication Flow

1. Open `/signup` to create an account
2. Choose role (`Student` or `Admin`)
3. Login via `/login`
4. Admin users can upload files; students can search/view

## Notes

- User database is created automatically at `backend/users.db`.
- Uploaded files are stored in `backend/uploads/`.


# Intelligent Campus Search Engine

A Flask-based campus utility portal with authentication, searchable document indexing, faculty/notices modules, and a map page with room-number route prompts.

## Overview

This project combines:

- Session-based login/signup for `Student` and `Admin`
- Document upload + indexing (admin)
- Search with keyword, prefix, and filename modes
- Campus modules (map, faculty, notices, notifications, profile)
- Route prompt generator on the map page for room codes like `C208`

## Current Features

### Authentication and Profile

- Signup and login with hashed passwords (`werkzeug.security`)
- Role support: `Student`, `Admin`
- Editable profile fields: name, phone, profile photo
- Academic details shown in profile: department, course, programme

### Search Engine

- Inverted index backed by custom data structures:
  - `HashTable`
  - `LinkedList` posting lists
  - `Trie` for autocomplete/prefix search
- Tokenization with stopword filtering
- Search modes:
  - Keyword search
  - Prefix search
  - Filename search
- Category inference from filename
- Result grouping by category in dashboard
- Live autocomplete endpoint

### Upload and File Access

- Admin-only document upload
- Supported uploads: `pdf`, `txt`, `doc`, `docx`, `ppt`, `pptx`, `xls`, `xlsx`, `png`, `jpg`, `jpeg`, `webp`, `gif`
- PDF text extraction via `PyPDF2`
- Secure file serving with allowlist checks
- Admin upload deletion with index rebuild for removed files

### Campus Modules

- Faculty directory with search and filters
- Notices page with pinned + latest sections
- Notifications page (marks notifications read)
- Bookmarks and recent search history in session

### Campus Map Route Finder (Updated)

- Room input prompt in map section: example `C208`
- Validates room format: `BlockLetter + 3 digits`
- Generates step-by-step route text dynamically
- Uses block-specific route profiles from backend:
  - Gate number
  - Entry hint
  - Stairs hint
  - Lift hint
  - Floor notes

Example style of output:

1. Go to C Block.
2. Take entry from Gate No. 1.
3. Take the main C Block entry beside the central plaza.
4. Take the stairs just after the entry gate and go to second floor.
5. Destination C208 is after 3 classes on your left.

## Project Structure

```text
backend/
  app.py
  database.py
  search_engine.py
  datastructure/
    hashtable.py
    linkedlist.py
    trie.py
  ingestion/
    pdfreader.py
  uploads/
    admin_uploaded_files/

frontend/
  templates/
    _navbar.html
    index.html
    campus_map.html
    faculty.html
    notices.html
    notifications.html
    profile.html
    login.html
    signup.html
  static/
    script.js
    style.css
    images/
      profiles/

README.md
```

## Tech Stack

- Python 3.9+
- Flask
- SQLite (via `sqlite3`, built-in)
- PyPDF2
- HTML, CSS, JavaScript

## Setup

From project root:

1. Create virtual environment

```bash
python -m venv .venv
```

2. Activate environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install flask pypdf2 python-dotenv
```

4. Create a `.env` file in the project root

```env
PORT=3000
API_KEY=your_secret_key_here
DATABASE_URL=mongodb://localhost:27017/myapp
SECRET_KEY=change-this-secret-key-before-production
```

`SECRET_KEY` is used by Flask for signed session cookies. `PORT` controls the local server port.

## Run

From project root:

```bash
python backend/app.py
```

Application URLs:

- `http://127.0.0.1:3000`
- `http://localhost:3000`

If `PORT` is not set, the app falls back to `5000`.

## Routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Dashboard |
| `/signup` | GET, POST | Register user |
| `/login` | GET, POST | Login user |
| `/logout` | GET | Logout and clear session |
| `/search` | GET | Search with filters/modes |
| `/autocomplete` | GET | Trie-based suggestions |
| `/campus-map` | GET | Campus map + room route prompts |
| `/faculty` | GET | Faculty listing and filters |
| `/notices` | GET | Notices page |
| `/notifications` | GET | Notifications page |
| `/profile` | GET, POST | Profile view/update |
| `/bookmark` | POST | Toggle bookmark item |
| `/clear-history` | POST | Clear recent searches |
| `/upload` | POST | Admin upload document |
| `/upload/delete` | POST | Admin delete uploaded file/folder |
| `/files/<path:filename>` | GET | View/download uploaded file |

## Data and Storage

- User database: `backend/users.db`
- Uploaded files:
  - `backend/uploads/admin_uploaded_files/` (current)
  - `backend/uploads/` (legacy compatibility)
- Profile images: `frontend/static/images/profiles/`

## Security Notes

- Passwords are stored as hashes
- Session cookies: HTTP-only, SameSite=Lax
- Admin-only protection on upload/delete routes
- File path normalization and directory boundary checks

## Notes

- Set `SECRET_KEY` in `.env` or your deployment environment for production.
- `SESSION_COOKIE_SECURE` is currently `False` for local development; set to `True` under HTTPS in production.
- The app loads `.env` automatically when `python-dotenv` is installed.
- This project currently uses in-memory search index population during runtime uploads. If app restarts, previously uploaded files remain on disk but are not auto-reindexed unless re-uploaded or indexed by custom startup logic.

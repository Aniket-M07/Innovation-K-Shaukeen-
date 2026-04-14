# Intelligent Campus Search Engine With Chatbot

Flask-based campus portal with authentication, role-based upload, custom document search, faculty lookup, notices, notifications, and profile management.

## Current Status

This README documents what is implemented in the current codebase.

Implemented now:

- Login/signup with `Student` and `Admin` roles (SQLite-backed).
- Admin-only upload/delete for campus files.
- Custom search engine using:
  - inverted index,
  - trie-based autocomplete and prefix matching,
  - weighted ranking combining keyword, prefix, and filename matches.
- Search filters in UI: category, department, service type, audience.
- Faculty directory page with query, department, and staff-room filters.
- Notices and notifications pages.
- Profile update flow (name, phone, profile picture).
- Session features: bookmarks, recent searches, basic search analytics counter.

Not implemented as a backend chatbot service yet:

- There is no dedicated chat API route in `backend/app.py` at this time.

## Tech Stack

- Python 3.9+
- Flask
- SQLite (`sqlite3`)
- PyPDF2
- python-dotenv (optional)
- HTML, CSS, JavaScript

## Project Structure

```text
.
|-- .env
|-- backend
|   |-- app.py
|   |-- database.py
|   |-- search_engine.py
|   |-- users.db
|   |-- datastructure
|   |   |-- __init__.py
|   |   |-- hashtable.py
|   |   |-- linkedlist.py
|   |   `-- trie.py
|   |-- ingestion
|   |   `-- pdfreader.py
|   `-- uploads
|       `-- admin_uploaded_files
|-- frontend
|   |-- static
|   |   |-- script.js
|   |   |-- style.css
|   |   `-- images
|   |       `-- profiles
|   `-- templates
|       |-- _navbar.html
|       |-- faculty.html
|       |-- index.html
|       |-- login.html
|       |-- notices.html
|       |-- notifications.html
|       |-- profile.html
|       `-- signup.html
`-- README.md
```

## Main Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Dashboard (login required) |
| `/signup` | GET, POST | User registration |
| `/login` | GET, POST | User login |
| `/logout` | GET | Logout |
| `/upload` | POST | Admin-only upload |
| `/upload/delete` | POST | Admin-only delete uploaded file/folder |
| `/search` | GET | Render search results page |
| `/api/search` | GET | JSON search results for inline UI |
| `/api/search-analytics` | POST | Store per-query usage count in session |
| `/autocomplete` | GET | Trie suggestions for current token |
| `/faculty` | GET | Faculty listing and filters |
| `/notices` | GET | Notices page |
| `/notifications` | GET | Notifications page (marks all as read) |
| `/profile` | GET, POST | Profile view/update |
| `/bookmark` | POST | Toggle bookmark item |
| `/clear-history` | POST | Clear recent search history |
| `/files/<path:filename>` | GET | Open/download uploaded files |

## Environment Variables

Example `.env`:

```env
SECRET_KEY=myprojectsecretkey
UPLOAD_FOLDER=uploads
DATABASE_URL=sqlite:///backend/users.db
PORT=5000
```

Notes:

- `SECRET_KEY` is used by Flask sessions.
- `PORT` is used by `app.run(...)`; default is `5000` if missing.
- `UPLOAD_FOLDER` and `DATABASE_URL` may exist in `.env`, but the current code paths are hardcoded in Python modules.

## Local Setup

1. Create virtual environment

```bash
python -m venv .venv
```

2. Activate it

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies

```bash
pip install flask pypdf2 python-dotenv
```

4. Run application

```bash
python backend/app.py
```

5. Open in browser

- `http://127.0.0.1:5000` (or your `PORT` value)

## Search and Upload Notes

- Allowed upload extensions:
  - `pdf`, `txt`, `doc`, `docx`, `ppt`, `pptx`, `xls`, `xlsx`, `png`, `jpg`, `jpeg`, `webp`, `gif`
- Uploaded files are saved in:
  - `backend/uploads/admin_uploaded_files/`
- Search index is runtime in-memory.
  - After server restart, old uploaded files remain on disk but are not auto-indexed until uploaded/indexed again by app logic.

## Security Notes

- Passwords are stored hashed (`werkzeug.security`).
- Set a strong `SECRET_KEY` in production.
- Set `SESSION_COOKIE_SECURE=True` when deploying over HTTPS.

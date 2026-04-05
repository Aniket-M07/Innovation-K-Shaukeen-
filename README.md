# Intelligent Campus Search Engine

A Flask-based campus portal that combines secure authentication, searchable campus documents, faculty lookup, notices, notifications, profile management, and a map room-route helper.

## What This Project Does

- User authentication with role support (`Student`, `Admin`)
- Admin document upload and delete with indexing into a custom search engine
- Search modes: keyword, prefix, filename, and category filtering
- Campus map page with room number route guidance (for codes like `C208`)
- Faculty directory with query + filters
- Notices and notifications modules
- User profile editing with optional profile image upload
- Session-based bookmarks and recent search history

## Tech Stack

- Python 3.9+
- Flask
- SQLite (`sqlite3`)
- PyPDF2
- python-dotenv
- HTML, CSS, JavaScript

## Project Structure

```text
.
├── .env
├── backend
│   ├── app.py
│   ├── database.py
│   ├── search_engine.py
│   ├── users.db
│   ├── datastructure
│   │   ├── __init__.py
│   │   ├── hashtable.py
│   │   ├── linkedlist.py
│   │   └── trie.py
│   ├── ingestion
│   │   └── pdfreader.py
│   └── uploads
│       └── admin_uploaded_files
├── frontend
│   ├── static
│   │   ├── logo.png
│   │   ├── script.js
│   │   ├── style.css
│   │   └── images
│   │       ├── image.png
│   │       ├── krmu logo.jpg
│   │       └── profiles
│   └── templates
│       ├── _navbar.html
│       ├── campus_map.html
│       ├── faculty.html
│       ├── index.html
│       ├── login.html
│       ├── notices.html
│       ├── notifications.html
│       ├── profile.html
│       └── signup.html
└── README.md
```

## Backend Overview

### `backend/app.py`

Main Flask application containing:

- App setup and folder paths
- Environment loading via `python-dotenv` (when installed)
- Session and auth configuration
- Search engine instance initialization
- Sample in-memory data for faculty, notices, notifications, map route profiles
- All web routes
- File upload/delete and serving logic

### `backend/database.py`

SQLite helper module:

- Initializes `users` table (with legacy column migration safeguards)
- Add/get/delete users
- Get user by email
- Update user profile
- Update user role

Database file location:

- `backend/users.db`

### `backend/search_engine.py`

Custom search engine implementation:

- Tokenization + stopword filtering
- Inverted index for term-to-doc mapping
- Trie for autocomplete/prefix search
- Ranking based on term frequency
- Category inference from filenames
- Document add/remove and index rebuild operations

### Custom Data Structures

- `backend/datastructure/hashtable.py`: custom hash table with resizing
- `backend/datastructure/linkedlist.py`: linked list + posting entries
- `backend/datastructure/trie.py`: trie for autocomplete

### PDF Ingestion

- `backend/ingestion/pdfreader.py`: safe PDF text extraction via `PyPDF2`

## Frontend Overview

### Templates

- `index.html`: dashboard, upload UI, search form, grouped results, news/gallery sections
- `campus_map.html`: map info + room route finder UI
- `faculty.html`: searchable/filterable faculty cards
- `notices.html`: pinned/latest notices with bookmark action
- `notifications.html`: notifications list
- `profile.html`: profile info + edit form + profile image upload
- `login.html`: login form
- `signup.html`: registration form
- `_navbar.html`: shared top navigation and session state links

### Static

- `script.js` includes:
  - autocomplete behavior
  - simulated voice search and clear button support
  - room route instruction generation based on block/floor
  - search loading UI helpers
  - upload form client-side validation hooks
- `style.css`: shared layout and module styling

## Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Dashboard (requires login) |
| `/signup` | GET, POST | Register account |
| `/login` | GET, POST | Login |
| `/logout` | GET | Logout + clear session |
| `/search` | GET | Search documents (keyword/prefix/filename/category) |
| `/autocomplete` | GET | Trie-backed term suggestions |
| `/upload` | POST | Admin-only file upload |
| `/upload/delete` | POST | Admin-only delete file/folder |
| `/campus-map` | GET | Campus map and route finder |
| `/faculty` | GET | Faculty listing with filters |
| `/notices` | GET | Notices page |
| `/notifications` | GET | Notifications page (marks all as read) |
| `/profile` | GET, POST | Profile view/update |
| `/bookmark` | POST | Toggle bookmark item |
| `/clear-history` | POST | Clear search history |
| `/files/<path:filename>` | GET | Open/download allowed uploaded file |

## Authentication and Sessions

- Passwords are hashed with `werkzeug.security`
- Session keys include user identity, role, profile info, bookmarks, and search history
- Session cookie settings:
  - `SESSION_COOKIE_HTTPONLY=True`
  - `SESSION_COOKIE_SAMESITE="Lax"`
  - `SESSION_COOKIE_SECURE=False` (set `True` in HTTPS production)
- Permanent session lifetime: 7 days

## Environment Variables

Create `.env` in project root:

```env
PORT=3000
API_KEY=your_secret_key_here
DATABASE_URL=mongodb://localhost:27017/myapp
SECRET_KEY=change-this-secret-key-before-production
```

Notes:

- `SECRET_KEY` is required for Flask session signing.
- `PORT` controls server port (`5000` fallback if unset).
- `API_KEY` and `DATABASE_URL` are currently present in `.env` but not consumed by backend logic yet.

## Setup

From project root:

1. Create virtual environment

```bash
python -m venv .venv
```

2. Activate virtual environment

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

4. Ensure `.env` exists (see above)

5. Run the app

```bash
python backend/app.py
```

## Access URLs

With `PORT=3000`:

- `http://127.0.0.1:3000`
- `http://localhost:3000`

If `PORT` is not set, default is `5000`.

## File Upload Behavior

Backend upload allowlist supports:

- `pdf`, `txt`, `doc`, `docx`, `ppt`, `pptx`, `xls`, `xlsx`, `png`, `jpg`, `jpeg`, `webp`, `gif`

Storage locations:

- Current admin uploads: `backend/uploads/admin_uploaded_files/`
- Legacy fallback reads: `backend/uploads/`

## Search Behavior

- Indexed fields: title, filename, and document content
- Query modes:
  - keyword search
  - prefix search via trie
  - filename search (contains or prefix)
- Category grouping in UI results
- Autocomplete endpoint returns term frequency

## Known Implementation Notes

- Indexed documents are in-memory at runtime; restart clears in-memory index until files are re-uploaded/re-indexed by custom logic.
- `script.js` upload client-side validation currently allows `pdf` and `txt`, while backend accepts a broader set.
- The static map panel is currently a placeholder; route guidance is text-based.

## Security Notes

- Keep `.env` private and do not commit real secrets.
- Use a strong random `SECRET_KEY` in production.
- Set `SESSION_COOKIE_SECURE=True` when serving over HTTPS.

# Intelligent Campus Search Engine - Smart Campus MVP

A modern Flask-based smart campus utility app that helps students quickly search and access campus-related information including faculty, classrooms, notices, events, and documents with an intuitive user interface.

## 🎯 Project Goal

Transform the campus experience with a practical MVP application that integrates document search, faculty directory, notices, event information, and campus resources in one clean, responsive interface.

## ✨ Features

### Core Features
- **User Authentication**: Session-based signup/login with roles (`Student` and `Admin`)
- **Profile Management**: Editable profiles with department, course, and programme information
- **Consistent Navigation**: Fixed navbar with active page indicator across all pages

### 🔍 Smart Search
- **Live Search Suggestions**: Real-time autocomplete as you type
- **Recent Search History**: Access frequently searched queries
- **Trending Searches**: Discover popular campus searches
- **Category Filtering**: Filter results by Faculty / Classrooms / Notices / Events / Documents
- **Voice Search**: Microphone button for voice input simulation
- **Clear Button**: Quick search field reset
- **Multiple Search Types**:
  - Keyword search (full-text)
  - Prefix search (autocomplete)
  - Filename search

### 📚 Search Result Categorization
- Results grouped into organized sections:
  - Faculty Results
  - Classroom Results
  - Notices
  - Events
  - Documents
- Each result card displays: title, icon, category, and quick actions

### 🎓 Campus Features
- **Campus Map**: Building locator, department finder, classroom and lab locator
- **Faculty Directory**: Searchable faculty list with:
  - Faculty name
  - Department
  - Cabin number
  - Availability status
- **Notices System**:
  - Latest notices
  - Pinned notices (priority)
  - Searchable notices
  - Category badges
- **Notifications**: Red dot indicator for unread notifications with notification screen

### 💾 Bookmarks & History
- **Bookmark Feature**: Save search results, notices, and faculty cards
- **Persistent Bookmarks**: Stored in user session
- **Recent Searches**: Track and access recently searched queries
- **Search History Clearing**: One-click clear recent searches

### 👤 Enhanced Profile
- **Profile Dashboard**: User information and activity overview
- **Profile Editing**:
  - Display name (editable)
  - Phone number (editable)
  - Email (locked for security)
  - Profile picture placeholder (UI ready)
- **Account Activity Section**:
  - Bookmarks list
  - Recent searches list
- **Academic Info Display**:
  - Department
  - Course
  - Programme

### 🎨 Modern UI/UX
- Clean, minimal design with consistent styling
- Responsive layout (desktop, tablet, mobile)
- Smooth animations and transitions
- Professional color scheme (dark blue & red)
- Proper spacing and typography

### 📱 Dashboard Experience
- **Greeting**: Time-based greeting (morning/afternoon/evening)
- **Quick Access**: Recent and trending searches
- **User Dashboard**: Quick campus resource access

## 🏗️ Project Architecture

```text
backend/
  app.py                    # Main Flask application with routes
  database.py              # User management and SQLite operations
  search_engine.py         # Campus search with category inference
  datastructure/
    hashtable.py          # Hash table for inverted index
    linkedlist.py         # Linked list for posting lists
    trie.py               # Trie for prefix search/autocomplete
  ingestion/
    pdfreader.py          # PDF text extraction
  uploads/                # Document storage

frontend/
  templates/
    _navbar.html          # Reusable navigation bar
    index.html            # Dashboard & search page
    campus_map.html       # Campus map viewer
    faculty.html          # Faculty directory
    notices.html          # Notices section
    notifications.html    # Notifications page
    profile.html          # User profile & settings
    login.html            # Login page
    signup.html           # Registration page
  static/
    style.css             # Modern, responsive styling
    script.js             # Interactive features & search logic
    images/               # Assets directory

README.md
requirements.txt (optional)
```

## 📋 Requirements

- Python 3.9+
- Flask
- PyPDF2 (for PDF extraction)
- sqlite3 (built-in)

## ⚙️ Setup Instructions

### 1. Create Virtual Environment

From the project root:

```bash
python -m venv .venv
```

### 2. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install flask pypdf2
```

## 🚀 Running the Application

From the project root:

```bash
python backend/app.py
```

The app will be available at:
- `http://127.0.0.1:5000`
- `http://localhost:5000`



## 🔐 Authentication Flow



1. Navigate to `/signup` to create a new account
2. Enter: name, email, password, role (Student/Admin)
3. Auto-login after signup or use `/login` page
4. Dashboard opens with smart search and campus resources
5. Admin users can upload documents via `/upload`
6. Students can search, bookmark, and explore campus info



## 📍 Available Routes



| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Dashboard with smart search |
| `/signup` | GET, POST | User registration |
| `/login` | GET, POST | User login |
| `/logout` | GET | Clear session |
| `/search` | GET | Search documents with filters |
| `/autocomplete` | GET | Real-time search suggestions |
| `/campus-map` | GET | Campus locations & buildings |
| `/faculty` | GET | Faculty directory |
| `/notices` | GET | Campus notices & announcements |
| `/notifications` | GET | Notifications center |
| `/profile` | GET, POST | User profile & settings |
| `/bookmark` | POST | Toggle bookmark status |
| `/upload` | POST | Admin document upload |
| `/files/<filename>` | GET | Download/view documents |



## 💡 Key Features Explained



### Smart Search
- Type in the search box to see live suggestions
- Click microphone (🎤) to simulate voice input
- Click X (✖) to clear the search field
- Select category filter to narrow results
- Use prefix/filename checkboxes for advanced search



### Faculty Search
- Search by faculty name, department, or cabin number
- View availability status (Available/In Meeting/On Leave)
- Bookmark faculty cards for quick access



### Bookmarking
- Click "Bookmark" button on any item (faculty, notice, document)
- View all bookmarks in Profile > Account Activity
- Bookmarks persist in current session



### Recent Searches
- Automatically tracked as you search
- Displayed on dashboard and profile
- Clear all with one click



## 🗄️ Database

The app uses SQLite (`backend/users.db`). The database is created automatically on first run with:

- **users table**: Stores user credentials, role, phone, department, course, programme
- Automatic schema creation with migration support for legacy databases



## 📁 File Structure Highlights

- `backend/app.py`: All Flask routes (search, faculty, notices, profile, etc.)
- `backend/database.py`: User management & profile updates
- `backend/search_engine.py`: Advanced search with category inference
- `frontend/templates/_navbar.html`: Reusable navbar component
- `frontend/static/style.css`: Comprehensive styling with responsive design
- `frontend/static/script.js`: Client-side search, autocomplete, voice simulation



## 🔒 Security Notes

- Passwords are hashed using werkzeug security
- Session cookies are HTTP-only and same-site
- Email is locked in profile editing
- Admin-only routes protected with decorator
- File uploads validated and secured



## 📝 License & Notes

- User database stored at: `backend/users.db`
- Uploaded documents stored at: `backend/uploads/`
- For production, set `SECRET_KEY` environment variable
- In development, default secret key is used (change in production)



## 🎯 MVP Features Implemented

✅ Smart Search Upgrade  
✅ Search Result Categorization  
✅ Voice Search Simulation  
✅ Campus Map Section  
✅ Faculty Finder  
✅ Notice System  
✅ Bookmark Feature  
✅ Notification System  
✅ Profile Improvements  
✅ Better Dashboard Experience  
✅ Modern UI Design  
✅ Consistent Navigation  
✅ Session-based History Tracking  
✅ Category-based Filtering  



## 🚧 Future Enhancements

- Real voice-to-text API integration
- Live campus map with actual coordinates
- Email notifications
- Advanced analytics dashboard
- Mobile app version
- Real-time notifications using WebSockets


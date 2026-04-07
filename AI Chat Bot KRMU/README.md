# Smart Campus AI

Smart Campus AI is a full-stack campus assistant with:
- React frontend (Vite)
- Node.js backend (Express + MySQL)
- Python AI engine (FastAPI + RAG + FAISS)
- Admin document upload, indexing, and retrieval
- User feedback loop to improve future responses
- Web fallback answers for general questions

---

## 1) Project Architecture

- Frontend: `src/` (React UI, chat, admin panel)
- Backend API: `backend/` (auth, chat, admin, feedback, MySQL)
- AI Engine: `ai_engine/` (embedding, retrieval, answer generation)
- Vector data: `ai_engine/data/` (FAISS index + metadata)

Runtime ports:
- Frontend: 5173
- Backend: 5000
- AI engine: 8000

---

## 2) Prerequisites

Install these first:
- Node.js 18+
- Python 3.11+ (3.13 works in your current setup)
- MySQL 8+
- Windows PowerShell (for commands below)

---

## 3) Environment Setup

### Root environment
Create or update `.env` in the project root:

```env
PORT=5000
JWT_SECRET=smart-campus-super-secret-key-change-me
JWT_EXPIRES_IN=7d

DB_HOST=localhost
DB_PORT=3306
DB_USER=smart_campus_user
DB_PASSWORD=your_db_password
DB_NAME=smart_campus_ai

AI_ENGINE_BASE_URL=http://127.0.0.1:8000
AI_ENGINE_TIMEOUT_MS=30000
```

### AI engine environment
Create or update `ai_engine/.env`:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

WEB_SEARCH_ENABLED=true
WEB_SEARCH_PROVIDER=duckduckgo
WEB_SEARCH_MAX_RESULTS=5
WEB_SEARCH_TIMEOUT_MS=8000

FEEDBACK_CONTEXT_LIMIT=10

CHUNK_SIZE=800
CHUNK_OVERLAP=120
DEFAULT_TOP_K=4
MIN_CONFIDENCE_THRESHOLD=0.55

FAISS_INDEX_PATH=ai_engine/data/faiss.index
FAISS_METADATA_PATH=ai_engine/data/faiss_metadata.json
```

Important:
- If OPENAI_API_KEY is missing, the app can still work with local/web fallback, but GPT quality will be limited.
- If OpenAI returns 429 insufficient_quota, enable billing/quota on your OpenAI account.

---

## 4) Install Dependencies

From project root:

```powershell
npm install
```

For AI engine Python packages:

```powershell
cd ai_engine
C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\python.exe -m pip install -r requirements.txt
cd ..
```

---

## 5) Database Setup

Create database and apply schema:

```sql
CREATE DATABASE IF NOT EXISTS smart_campus_ai;
```

Then run schema file from MySQL client:

```powershell
Get-Content .\backend\sql\schema.sql | mysql -u smart_campus_user -p smart_campus_ai
```

---

## 6) Run Application (All Services)

Open three terminals.

### Terminal A: Backend
```powershell
cd "c:\Users\LENOVO\Desktop\AI Chat Bot KRMU"
npm run server
```

### Terminal B: Frontend
```powershell
cd "c:\Users\LENOVO\Desktop\AI Chat Bot KRMU"
npm run dev
```

### Terminal C: AI Engine
```powershell
cd "c:\Users\LENOVO\Desktop\AI Chat Bot KRMU\ai_engine"
C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Copy note:
- Run only the two lines inside the code block above.
- Do not copy markdown markers (```powershell / ```) or the health-check lines into terminal.

Health checks:
- Backend: http://localhost:5000/api/health
- AI engine: http://127.0.0.1:8000/health
- Frontend: http://localhost:5173

---

## 7) Phone Access

Use your LAN IP (example: `10.18.28.59`) and ensure phone is on same Wi-Fi:
- Frontend: http://10.18.28.59:5173

If phone cannot access:
1. Confirm backend/frontend are listening on 0.0.0.0
2. Allow firewall inbound ports 5173, 5000, 8000 (run as Administrator)

```powershell
netsh advfirewall firewall add rule name="SmartCampusAI Frontend 5173" dir=in action=allow protocol=TCP localport=5173
netsh advfirewall firewall add rule name="SmartCampusAI Backend 5000" dir=in action=allow protocol=TCP localport=5000
netsh advfirewall firewall add rule name="SmartCampusAI AIEngine 8000" dir=in action=allow protocol=TCP localport=8000
```

---

## 8) Admin and User Flow

- Register users from Register page (student role by default).
- Admins create additional admins from Admin Dashboard.
- Admin uploads documents for indexing.
- Users ask questions in chat.
- Answers include source metadata and support feedback.

---

## 9) Feedback Loop

- Users can rate AI responses (1 to 5) and add comments.
- Feedback is stored in MySQL `feedback` table.
- Recent feedback context is injected into future AI prompts.

---

## 10) Answer Modes

The AI can answer from:
- Documents (RAG over uploaded files)
- Web fallback (general questions)
- GPT (if OPENAI_API_KEY and quota are available)

If GPT quota is unavailable, the system gracefully falls back instead of crashing.

---

## 11) Common Issues

### A) Document upload fails during embedding
- Check AI engine health endpoint
- Ensure AI engine is running
- Ensure document contains extractable text
- Verify OPENAI_API_KEY if GPT embeddings are needed

### B) OPENAI_API_KEY missing
- Add key in `ai_engine/.env`
- Restart AI engine

### C) OpenAI 429 insufficient_quota
- Add billing or increase quota on OpenAI account
- App will still work with fallback modes

### D) Port already in use (WinError 10048)
Kill process using the port:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object -ExpandProperty OwningProcess
Stop-Process -Id <PID> -Force
```

### E) AI responses look irrelevant
- Re-upload cleaner documents
- Ask more specific campus questions
- Ensure feedback is being submitted
- Enable GPT mode for better synthesis

---

## 12) Build Frontend

```powershell
cd "c:\Users\LENOVO\Desktop\AI Chat Bot KRMU"
npm run build
```

Output is generated in `dist/`.

---

## 13) Security Notes

- Never commit real API keys to Git.
- Rotate keys immediately if exposed.
- Keep `.env` and `ai_engine/.env` private.

---

## 14) Quick Start (Copy/Paste)

```powershell
# 1) Backend
cd "c:\Users\LENOVO\Desktop\AI Chat Bot KRMU"
npm run server

# 2) Frontend (new terminal)
cd "c:\Users\LENOVO\Desktop\AI Chat Bot KRMU"
npm run dev

# 3) AI Engine (new terminal)
cd "c:\Users\LENOVO\Desktop\AI Chat Bot KRMU\ai_engine"
C:\Users\LENOVO\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open: http://localhost:5173

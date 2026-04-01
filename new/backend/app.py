import os
from functools import wraps
from datetime import timedelta

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from ingestion.pdfreader import extract_text_from_pdf
from search_engine import CampusSearchEngine
from database import init_db, add_user, get_user, get_user_by_email


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"pdf", "txt"}


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")


def ensure_upload_dir() -> None:
	if not os.path.isdir(UPLOAD_DIR):
		os.makedirs(UPLOAD_DIR, exist_ok=True)


def allowed_file(filename: str) -> bool:
	if "." not in filename:
		return False
	ext = filename.rsplit(".", 1)[1].lower()
	return ext in ALLOWED_EXTENSIONS


def read_text_file(path: str) -> str:
	with open(path, "r", encoding="utf-8", errors="ignore") as file:
		return file.read()


app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR, static_url_path='/static')
search_index = CampusSearchEngine()

# Sample campus directory and notifications for MVP
FACULTY_DIRECTORY = [
	{"name": "Dr. Anita Sharma", "department": "Computer Science", "cabin": "C-201", "availability": "Available"},
	{"name": "Prof. Rajesh Kumar", "department": "Mechanical Engineering", "cabin": "M-105", "availability": "In Meeting"},
	{"name": "Dr. Nisha Verma", "department": "Mathematics", "cabin": "B-302", "availability": "Available"},
	{"name": "Dr. Sunita Singh", "department": "Physics", "cabin": "P-112", "availability": "On Leave"},
	{"name": "Mr. Rahul Gupta", "department": "Civil Engineering", "cabin": "C-114", "availability": "Available"},
]

NOTICES = [
	{"id": 1, "title": "Exam Schedule Released", "category": "Academic", "content": "Check the new exam schedule in your department.", "pinned": True},
	{"id": 2, "title": "Library Extended Hours", "category": "Library", "content": "Library now open till 10 PM on weekdays.", "pinned": False},
	{"id": 3, "title": "Guest Lecture on AI", "category": "Events", "content": "Join the AI guest lecture this Friday at the auditorium.", "pinned": True},
	{"id": 4, "title": "Sports Day Update", "category": "Campus Life", "content": "Sports day registrations open until next Wednesday.", "pinned": False},
]

NOTIFICATIONS = [
	{"id": 1, "title": "New notice added: Exam Schedule", "read": False},
	{"id": 2, "title": "Profile preferences updated", "read": True},
	{"id": 3, "title": "New document uploaded to repository", "read": False},
]

TRENDING_SEARCHES = ["AI syllabus", "Campus map", "Library hours", "Faculty contact", "Notice board"]

# ===== ADD CONFIGURATION FOR SESSIONS AND AUTHENTICATION =====
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# Initialize the database
init_db()


# ===== AUTHENTICATION DECORATORS =====
def login_required(f):
	"""Decorator to require user to be logged in"""
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if "user_id" not in session:
			return redirect(url_for("login"))
		return f(*args, **kwargs)
	return decorated_function


def admin_required(f):
	"""Decorator to require user to be logged in as Admin"""
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if "user_id" not in session:
			return redirect(url_for("login"))
		if session.get("role") != "Admin":
			abort(403)  # Forbidden
		return f(*args, **kwargs)
	return decorated_function


def _get_greeting():
	from datetime import datetime
	hour = datetime.now().hour
	if hour < 12:
		return "Good morning"
	if hour < 17:
		return "Good afternoon"
	return "Good evening"


def _get_recent_searches():
	return session.get("recent_searches", [])[-6:][::-1]


def _get_bookmarks():
	return session.get("bookmarks", [])


def _pending_notifications_count():
	unread = [n for n in NOTIFICATIONS if not n.get("read")]
	return len(unread)


@app.route("/")
@login_required
def index():
	return render_template(
		"index.html",
		total_docs=len(search_index.documents),
		results=[],
		grouped_results={},
		query="",
		prefix=False,
		filename=False,
		user_role=session.get("role"),
		user_name=session.get("user_name", "Student"),
		greeting=_get_greeting(),
		recent_searches=_get_recent_searches(),
		trending_searches=TRENDING_SEARCHES,
		bookmarks=_get_bookmarks(),
		notifications_count=_pending_notifications_count(),
		active_page="dashboard",
	)


# ===== AUTHENTICATION ROUTES =====
@app.route("/signup", methods=["GET", "POST"])
def signup():
	"""Handle user registration"""
	if request.method == "GET":
		# Check if already logged in
		if "user_id" in session:
			return redirect(url_for("index"))
		return render_template("signup.html", errors=[])
	
	# POST request - process registration
	name = request.form.get("name", "").strip()
	email = request.form.get("email", "").strip()
	password = request.form.get("password", "")
	confirm_password = request.form.get("confirm-password", "")
	role = request.form.get("role", "Student")  # Student or Admin
	phone = request.form.get("phone", "").strip()
	department = request.form.get("department", "").strip()
	course = request.form.get("course", "").strip()
	programme = request.form.get("programme", "").strip()
	
	# Validate inputs
	errors = []
	
	if not name or len(name) < 2:
		errors.append("Name must be at least 2 characters long")
	
	if not email or "@" not in email:
		errors.append("Please provide a valid email address")
	
	if not password or len(password) < 6:
		errors.append("Password must be at least 6 characters long")
	
	if password != confirm_password:
		errors.append("Passwords do not match")
	
	if role not in ["Student", "Admin"]:
		errors.append("Invalid role selected")
	
	# Check if email already exists
	if not errors and get_user_by_email(email):
		errors.append("Email already registered")
	
	if errors:
		return render_template("signup.html", errors=errors), 400
	
	# Hash password and add user to database
	hashed_password = generate_password_hash(password)
	success, message = add_user(name, email, hashed_password, role, phone=phone, department=department, course=course, programme=programme)
	
	if success:
		# Auto-login after signup
		session["user_id"] = email
		session["user_name"] = name
		session["role"] = role
		session.permanent = True
		return redirect(url_for("index"))
	else:
		return render_template("signup.html", errors=[message]), 400


@app.route("/login", methods=["GET", "POST"])
def login():
	"""Handle user login"""
	if request.method == "GET":
		# Check if already logged in
		if "user_id" in session:
			return redirect(url_for("index"))
		return render_template("login.html", errors=[])
	
	# POST request - process login
	email = request.form.get("email", "").strip()
	password = request.form.get("password", "")
	remember = request.form.get("remember")
	
	errors = []
	
	if not email or not password:
		errors.append("Email and password are required")
	
	if errors:
		return render_template("login.html", errors=errors), 400
	
	# Query database for user (get hashed password)
	user = get_user_by_email(email)
	
	if not user:
		return render_template("login.html", errors=["Invalid email or password"]), 401
	
	# Verify password
	if not check_password_hash(user["password"], password):
		return render_template("login.html", errors=["Invalid email or password"]), 401
	
	# Login successful - create session
	session["user_id"] = user["email"]
	session["user_name"] = user["name"]
	session["role"] = user["role"]
	session["phone"] = user.get("phone", "")
	session["department"] = user.get("department", "")
	session["course"] = user.get("course", "")
	session["programme"] = user.get("programme", "")
	session.permanent = remember is not None
	
	return redirect(url_for("index"))


@app.route("/logout")
def logout():
	"""Clear session and logout user"""
	session.clear()
	return redirect(url_for("login"))


@app.route("/upload", methods=["POST"])
@admin_required
def upload():
	ensure_upload_dir()
	if "file" not in request.files:
		return redirect(url_for("index"))
	file = request.files["file"]
	if file.filename == "":
		return redirect(url_for("index"))
	if not allowed_file(file.filename):
		return redirect(url_for("index"))

	filename = secure_filename(file.filename)
	path = os.path.join(UPLOAD_DIR, filename)
	file.save(path)

	ext = filename.rsplit(".", 1)[1].lower()
	if ext == "pdf":
		content = extract_text_from_pdf(path)
	else:
		content = read_text_file(path)

	title = os.path.splitext(filename)[0]
	search_index.add_document(title=title, content=content, filename=filename)
	return redirect(url_for("index"))

@app.route("/search")
@login_required
def search():
	query = request.args.get("q", "").strip()
	prefix = request.args.get("prefix") == "1"
	use_filename = request.args.get("filename") == "1"
	category_filter = request.args.get("category", "All")

	if query:
		# keep most recent searches in session
		recent = session.get("recent_searches", [])
		if query not in recent:
			recent.append(query)
			if len(recent) > 20:
				recent.pop(0)
			session["recent_searches"] = recent

	if use_filename:
		ranked = search_index.filename_search(query, prefix=prefix)
	else:
		ranked = search_index.prefix_search(query) if prefix else search_index.keyword_search(query)

	results = []
	for doc_id, score in ranked:
		meta = search_index.documents.get(doc_id)
		if not meta:
			continue
		if category_filter and category_filter != "All" and meta.get("category") != category_filter:
			continue
		results.append({
			"title": meta["title"],
			"filename": meta["filename"],
			"score": score,
			"category": meta.get("category", "Documents"),
			"snippet": "Search terms matched in document index",
		})

	grouped_results = {}
	for item in results:
		cat = item.get("category", "Documents")
		grouped_results.setdefault(cat, []).append(item)

	return render_template(
		"index.html",
		total_docs=len(search_index.documents),
		results=results,
		grouped_results=grouped_results,
		query=query,
		prefix=prefix,
		filename=use_filename,
		category_filter=category_filter,
		user_role=session.get("role"),
		user_name=session.get("user_name", "Student"),
		greeting=_get_greeting(),
		recent_searches=_get_recent_searches(),
		trending_searches=TRENDING_SEARCHES,
		bookmarks=_get_bookmarks(),
		notifications_count=_pending_notifications_count(),
		active_page="dashboard",
	)


@app.route("/campus-map")
@login_required
def campus_map():
	map_locations = [
		{"name": "Main Library", "type": "Library", "building": "A"},
		{"name": "Engineering Block", "type": "Department", "building": "B"},
		{"name": "Lecture Hall 1", "type": "Classroom", "building": "C"},
		{"name": "Computer Lab", "type": "Lab", "building": "D"},
		{"name": "Sports Complex", "type": "Facility", "building": "E"},
	]
	return render_template("campus_map.html", locations=map_locations, active_page="map")


@app.route("/faculty")
@login_required
def faculty():
	q = request.args.get("q", "").lower()
	if q:
		matches = [f for f in FACULTY_DIRECTORY if q in f["name"].lower() or q in f["department"].lower() or q in f["cabin"].lower()]
	else:
		matches = FACULTY_DIRECTORY
	return render_template("faculty.html", faculty=matches, query=q, active_page="faculty")


@app.route("/notices")
@login_required
def notices():
	q = request.args.get("q", "").lower()
	if q:
		matches = [n for n in NOTICES if q in n["title"].lower() or q in n["category"].lower() or q in n["content"].lower()]
	else:
		matches = NOTICES
	pinned = [n for n in matches if n.get("pinned")]
	latest = [n for n in matches if not n.get("pinned")]
	return render_template("notices.html", pinned=pinned, latest=latest, query=q, active_page="notices")


@app.route("/notifications")
@login_required
def notifications():
	for n in NOTIFICATIONS:
		n["read"] = True
	return render_template("notifications.html", notifications=NOTIFICATIONS, active_page="notifications")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
	if request.method == "POST":
		if request.form.get("profile_update"):
			name = request.form.get("name", session.get("user_name", ""))
			phone = request.form.get("phone", session.get("phone", ""))

			# update DB
			from database import update_user_profile
			success, message = update_user_profile(
				email=session.get("user_id"),
				name=name,
				phone=phone,
			)
			if success:
				session["user_name"] = name
				session["phone"] = phone
			return redirect(url_for("profile"))

	return render_template(
		"profile.html",
		user_name=session.get("user_name", "Student"),
		user_email=session.get("user_id", ""),
		role=session.get("role", "Student"),
		phone=session.get("phone", ""),
		department=session.get("department", "") if session.get("department") else "N/A",
		course=session.get("course", "") if session.get("course") else "N/A",
		programme=session.get("programme", "") if session.get("programme") else "N/A",
		bookmarks=_get_bookmarks(),
		recent_searches=_get_recent_searches(),
		trend=TRENDING_SEARCHES,
		active_page="profile",
	)


@app.route("/bookmark", methods=["POST"])
@login_required
def toggle_bookmark():
	item_title = request.form.get("title") or request.form.get("item")
	item_type = request.form.get("type", "general")
	if not item_title:
		return redirect(request.referrer or url_for("index"))
	bookmarks = session.get("bookmarks", [])
	existing = next((b for b in bookmarks if b.get("title") == item_title and b.get("type") == item_type), None)
	if existing:
		bookmarks = [b for b in bookmarks if not (b.get("title") == item_title and b.get("type") == item_type)]
	else:
		bookmarks.append({"title": item_title, "type": item_type})
	session["bookmarks"] = bookmarks
	return redirect(request.referrer or url_for("index"))


@app.route("/clear-history", methods=["POST"])
@login_required
def clear_history():
	session["recent_searches"] = []
	return redirect(request.referrer or url_for("index"))


@app.route("/autocomplete")
@login_required
def autocomplete():
	query = request.args.get("q", "")
	if not query:
		return jsonify({"suggestions": []})

	last_token = query.strip().split()[-1].lower() if query.strip() else ""
	suggestions = search_index.trie.autocomplete(last_token, limit=8)
	return jsonify({
		"suggestions": [
			{"term": term, "frequency": frequency} for term, frequency in suggestions
		]
	})


@app.route("/files/<path:filename>")
@login_required
def serve_file(filename: str):
	if not allowed_file(filename):
		abort(404)
	path = os.path.join(UPLOAD_DIR, filename)
	if not os.path.isfile(path):
		abort(404)
	as_attachment = request.args.get("download") == "1"
	return send_from_directory(UPLOAD_DIR, filename, as_attachment=as_attachment)


if __name__ == "__main__":
	ensure_upload_dir()
	app.run(host="0.0.0.0", port=5000, debug=True)


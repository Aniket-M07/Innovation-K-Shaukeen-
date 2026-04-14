import os
import shutil
from functools import wraps
from datetime import timedelta
from uuid import uuid4

try:
	from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
	load_dotenv = None

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from ingestion.pdfreader import extract_text_from_pdf
from search_engine import CampusSearchEngine
from database import init_db, add_user, get_user, get_user_by_email


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
ADMIN_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "admin_uploaded_files")
PROFILE_IMAGE_DIR = os.path.join(STATIC_DIR, "images", "profiles")
ALLOWED_EXTENSIONS = {
	"pdf",
	"txt",
	"doc",
	"docx",
	"ppt",
	"pptx",
	"xls",
	"xlsx",
	"png",
	"jpg",
	"jpeg",
	"webp",
	"gif",
}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


if load_dotenv is not None:
	load_dotenv()


def ensure_upload_dir() -> None:
	if not os.path.isdir(UPLOAD_DIR):
		os.makedirs(UPLOAD_DIR, exist_ok=True)
	if not os.path.isdir(ADMIN_UPLOAD_DIR):
		os.makedirs(ADMIN_UPLOAD_DIR, exist_ok=True)
	if not os.path.isdir(PROFILE_IMAGE_DIR):
		os.makedirs(PROFILE_IMAGE_DIR, exist_ok=True)


def allowed_file(filename: str) -> bool:
	if "." not in filename:
		return False
	ext = filename.rsplit(".", 1)[1].lower()
	return ext in ALLOWED_EXTENSIONS


def read_text_file(path: str) -> str:
	with open(path, "r", encoding="utf-8", errors="ignore") as file:
		return file.read()


def _is_within_directory(path: str, base_dir: str) -> bool:
	base_dir = os.path.abspath(base_dir)
	path = os.path.abspath(path)
	return os.path.commonpath([path, base_dir]) == base_dir


def _resolve_admin_upload_path(relative_path: str) -> str:
	cleaned = os.path.normpath(relative_path.replace("\\", os.sep).replace("/", os.sep))
	if not cleaned or cleaned in {".", os.pardir}:
		abort(400)
	if os.path.isabs(cleaned) or cleaned.startswith(f"{os.pardir}{os.sep}"):
		abort(400)
	path = os.path.abspath(os.path.join(ADMIN_UPLOAD_DIR, cleaned))
	if not _is_within_directory(path, ADMIN_UPLOAD_DIR):
		abort(400)
	return path


def get_uploaded_files():
	"""Return uploaded document metadata sorted by newest first."""
	ensure_upload_dir()
	items = []
	seen_files = {}

	if os.path.isdir(ADMIN_UPLOAD_DIR):
		for entry in os.scandir(ADMIN_UPLOAD_DIR):
			if entry.is_dir():
				items.append({
					"filename": entry.name,
					"path": entry.name,
					"kind": "folder",
					"size_kb": None,
					"updated_at": entry.stat().st_mtime,
				})
				continue
			if not allowed_file(entry.name):
				continue
			seen_files[entry.name] = {
				"filename": entry.name,
				"path": entry.name,
				"kind": "file",
				"size_kb": max(1, round(entry.stat().st_size / 1024)),
				"updated_at": entry.stat().st_mtime,
			}

	if os.path.isdir(UPLOAD_DIR):
		for entry in os.scandir(UPLOAD_DIR):
			if entry.is_file() and allowed_file(entry.name) and entry.name not in seen_files:
				seen_files[entry.name] = {
					"filename": entry.name,
					"path": entry.name,
					"kind": "file",
					"size_kb": max(1, round(entry.stat().st_size / 1024)),
					"updated_at": entry.stat().st_mtime,
				}

	items.extend(seen_files.values())
	return sorted(items, key=lambda item: item["updated_at"], reverse=True)


def allowed_image_file(filename: str) -> bool:
	if "." not in filename:
		return False
	ext = filename.rsplit(".", 1)[1].lower()
	return ext in ALLOWED_IMAGE_EXTENSIONS


app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR, static_url_path='/static')
search_index = CampusSearchEngine()

# Sample campus directory and notifications for MVP
FACULTY_DIRECTORY = [
	{"name": "Dr. Anita Sharma", "department": "Computer Science", "cabin": "C-201", "staff_room": "B211", "contact": "9234587800", "email": "anita@ggmail.com", "availability": "Available"},
	{"name": "Prof. Rajesh Kumar", "department": "Mechanical Engineering", "cabin": "M-105", "staff_room": "B312", "contact": "9876543210", "email": "rajesh@college.com", "availability": "In Meeting"},
	{"name": "Dr. Nisha Verma", "department": "Mathematics", "cabin": "B-302", "staff_room": "A108", "contact": "9123456789", "email": "nisha@college.com", "availability": "Available"},
	{"name": "Dr. Sunita Singh", "department": "Physics", "cabin": "P-112", "staff_room": "C404", "contact": "9456789012", "email": "sunita@college.com", "availability": "On Leave"},
	{"name": "Mr. Rahul Gupta", "department": "Civil Engineering", "cabin": "C-114", "staff_room": "D205", "contact": "9789012345", "email": "rahul@college.com", "availability": "Available"},
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

TRENDING_SEARCHES = ["AI syllabus", "Library hours", "Faculty contact", "Notice board"]

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


def _announcement_items():
	return [notice for notice in NOTICES if notice.get("pinned")][:2]


def _ai_suggested_resources(user_name: str):
	bookmarks = _get_bookmarks()
	recent_searches = _get_recent_searches()
	suggestions = []

	if bookmarks:
		suggestions.extend([f"Because you bookmarked: {item.get('title', 'Resource')}" for item in bookmarks[:2]])

	if recent_searches:
		suggestions.append(f"Continue exploring: {recent_searches[0]}")

	suggestions.extend([
		"Try 'Scholarship deadlines' for current funding opportunities",
		"Explore 'IT support hours' for live help desk availability",
		f"Welcome back {user_name}, start with your most used services",
	])

	unique = []
	for item in suggestions:
		if item not in unique:
			unique.append(item)
	return unique[:5]


def _smart_ranked_search(query: str):
	query = query.strip()
	if not query:
		return []

	combined_scores = {}

	def add_scores(matches, weight: int, base_bonus: int = 0):
		for doc_id, score in matches:
			combined_scores[doc_id] = combined_scores.get(doc_id, 0) + (score * weight) + base_bonus

	# Run all supported search modes automatically and rank by weighted relevance.
	add_scores(search_index.keyword_search(query), weight=5)
	add_scores(search_index.prefix_search(query), weight=3)
	add_scores(search_index.filename_search(query, prefix=False), weight=6, base_bonus=2)
	add_scores(search_index.filename_search(query, prefix=True), weight=8, base_bonus=3)

	lower_query = query.lower()
	for doc_id, meta in search_index.documents.items():
		title = meta.get("title", "").lower()
		filename = meta.get("filename", "").lower()
		if lower_query and (title == lower_query or filename == lower_query):
			combined_scores[doc_id] = combined_scores.get(doc_id, 0) + 20

	return sorted(combined_scores.items(), key=lambda item: item[1], reverse=True)


def _extract_resource_facets(meta: dict):
	title = (meta.get("title") or "").lower()
	filename = (meta.get("filename") or "").lower()
	category = (meta.get("category") or "").lower()
	text = f"{title} {filename} {category}"

	department = "General"
	if any(keyword in text for keyword in ["library", "book", "catalog"]):
		department = "Library"
	elif any(keyword in text for keyword in ["it", "tech", "system", "portal"]):
		department = "IT"
	elif any(keyword in text for keyword in ["finance", "fee", "scholarship", "aid"]):
		department = "Finance"
	elif any(keyword in text for keyword in ["health", "medical", "wellness"]):
		department = "Health"
	elif any(keyword in text for keyword in ["advising", "academic", "faculty"]):
		department = "Academic"

	service_type = "Information"
	if any(keyword in text for keyword in ["form", "registration", "apply", "application"]):
		service_type = "Administrative"
	elif any(keyword in text for keyword in ["support", "help", "ticket"]):
		service_type = "Support"
	elif any(keyword in text for keyword in ["event", "workshop", "seminar"]):
		service_type = "Events"

	audience = "All"
	if "faculty" in text or "staff" in text:
		audience = "Faculty/Staff"
	elif "student" in text or "scholarship" in text:
		audience = "Students"

	return {
		"department": department,
		"service_type": service_type,
		"audience": audience,
	}


def _collect_search_results(
	query: str,
	category_filter: str = "All",
	department_filter: str = "All",
	service_type_filter: str = "All",
	audience_filter: str = "All",
):
	ranked = _smart_ranked_search(query)
	results = []
	for doc_id, score in ranked:
		meta = search_index.documents.get(doc_id)
		if not meta:
			continue
		if category_filter and category_filter != "All" and meta.get("category") != category_filter:
			continue
		facets = _extract_resource_facets(meta)
		if department_filter != "All" and facets.get("department") != department_filter:
			continue
		if service_type_filter != "All" and facets.get("service_type") != service_type_filter:
			continue
		if audience_filter != "All" and facets.get("audience") != audience_filter:
			continue
		results.append({
			"title": meta["title"],
			"filename": meta["filename"],
			"score": score,
			"category": meta.get("category", "Documents"),
			"department": facets.get("department"),
			"service_type": facets.get("service_type"),
			"audience": facets.get("audience"),
			"snippet": "Search terms matched in document index",
		})

	grouped_results = {}
	for item in results:
		cat = item.get("category", "Documents")
		grouped_results.setdefault(cat, []).append(item)

	return results, grouped_results


@app.route("/")
@login_required
def index():
	uploaded_files = get_uploaded_files() if session.get("role") == "Admin" else []
	return render_template(
		"index.html",
		total_files=len([item for item in get_uploaded_files() if item.get("kind") == "file"]),
		uploaded_files=uploaded_files,
		results=[],
		grouped_results={},
		query="",
		category_filter="All",
		department_filter="All",
		service_type_filter="All",
		audience_filter="All",
		user_role=session.get("role"),
		user_name=session.get("user_name", "Student"),
		greeting=_get_greeting(),
		recent_searches=_get_recent_searches(),
		trending_searches=TRENDING_SEARCHES,
		announcement_items=_announcement_items(),
		ai_suggested_resources=_ai_suggested_resources(session.get("user_name", "Student")),
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
		session["profile_image"] = ""
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
	session["profile_image"] = user.get("profile_image", "")
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
	path = os.path.join(ADMIN_UPLOAD_DIR, filename)
	file.save(path)

	ext = filename.rsplit(".", 1)[1].lower()
	if ext == "pdf":
		content = extract_text_from_pdf(path)
	else:
		content = read_text_file(path)

	title = os.path.splitext(filename)[0]
	search_index.add_document(title=title, content=content, filename=filename)
	return redirect(url_for("index"))


@app.route("/upload/delete", methods=["POST"])
@admin_required
def delete_uploaded_item():
	ensure_upload_dir()
	target_path = request.form.get("path", "").strip()
	if not target_path:
		abort(400)

	filename = None
	admin_path = _resolve_admin_upload_path(target_path)
	if os.path.isdir(admin_path):
		shutil.rmtree(admin_path)
	else:
		candidates = [admin_path]
		if os.sep not in target_path and "/" not in target_path and "\\" not in target_path:
			candidates.append(os.path.abspath(os.path.join(UPLOAD_DIR, os.path.basename(target_path))))

		deleted = False
		for candidate in candidates:
			if os.path.isfile(candidate):
				os.remove(candidate)
				deleted = True
				filename = os.path.basename(candidate)

		if not deleted:
			abort(404)

	if filename:
		search_index.remove_document_by_filename(filename)

	return redirect(url_for("index"))

@app.route("/search")
@login_required
def search():
	query = request.args.get("q", "").strip()
	category_filter = request.args.get("category", "All")
	department_filter = request.args.get("department", "All")
	service_type_filter = request.args.get("service_type", "All")
	audience_filter = request.args.get("audience", "All")

	if query:
		# keep most recent searches in session
		recent = session.get("recent_searches", [])
		if query not in recent:
			recent.append(query)
			if len(recent) > 20:
				recent.pop(0)
			session["recent_searches"] = recent

	results, grouped_results = _collect_search_results(
		query,
		category_filter,
		department_filter,
		service_type_filter,
		audience_filter,
	)

	return render_template(
		"index.html",
		total_files=len([item for item in get_uploaded_files() if item.get("kind") == "file"]),
		uploaded_files=get_uploaded_files() if session.get("role") == "Admin" else [],
		results=results,
		grouped_results=grouped_results,
		query=query,
		category_filter=category_filter,
		department_filter=department_filter,
		service_type_filter=service_type_filter,
		audience_filter=audience_filter,
		user_role=session.get("role"),
		user_name=session.get("user_name", "Student"),
		greeting=_get_greeting(),
		recent_searches=_get_recent_searches(),
		trending_searches=TRENDING_SEARCHES,
		announcement_items=_announcement_items(),
		ai_suggested_resources=_ai_suggested_resources(session.get("user_name", "Student")),
		bookmarks=_get_bookmarks(),
		notifications_count=_pending_notifications_count(),
		active_page="dashboard",
	)


@app.route("/api/search")
@login_required
def api_search():
	query = request.args.get("q", "").strip()
	category_filter = request.args.get("category", "All")
	department_filter = request.args.get("department", "All")
	service_type_filter = request.args.get("service_type", "All")
	audience_filter = request.args.get("audience", "All")

	if query:
		recent = session.get("recent_searches", [])
		if query not in recent:
			recent.append(query)
			if len(recent) > 20:
				recent.pop(0)
			session["recent_searches"] = recent

	results, grouped_results = _collect_search_results(
		query,
		category_filter,
		department_filter,
		service_type_filter,
		audience_filter,
	)
	return jsonify({
		"query": query,
		"category_filter": category_filter,
		"department_filter": department_filter,
		"service_type_filter": service_type_filter,
		"audience_filter": audience_filter,
		"results": results,
		"grouped_results": grouped_results,
		"ai_suggested_resources": _ai_suggested_resources(session.get("user_name", "Student")),
		"count": len(results),
	})


@app.route("/api/search-analytics", methods=["POST"])
@login_required
def api_search_analytics():
	payload = request.get_json(silent=True) or {}
	query = (payload.get("query") or "").strip()
	if not query:
		return jsonify({"status": "ignored"})

	analytics = session.get("search_analytics", {})
	analytics[query] = analytics.get(query, 0) + 1
	session["search_analytics"] = analytics
	return jsonify({"status": "ok"})

@app.route("/faculty")
@login_required
def faculty():
	q = request.args.get("q", "").lower()
	department_filter = request.args.get("department", "")
	staff_room_filter = request.args.get("staff_room", "")
	
	matches = FACULTY_DIRECTORY
	
	# Filter by search query
	if q:
		matches = [f for f in matches if q in f["name"].lower() or q in f["department"].lower() or q in f["cabin"].lower() or q in f["contact"].lower() or q in f["email"].lower()]
	
	# Filter by department
	if department_filter:
		matches = [f for f in matches if f["department"] == department_filter]
	
	# Filter by staff room
	if staff_room_filter:
		matches = [f for f in matches if f["staff_room"] == staff_room_filter]
	
	# Get unique departments and staff rooms for filter options
	departments = sorted(list(set(f["department"] for f in FACULTY_DIRECTORY)))
	staff_rooms = sorted(list(set(f["staff_room"] for f in FACULTY_DIRECTORY)))
	
	return render_template(
		"faculty.html",
		faculty=matches,
		query=q,
		department_filter=department_filter,
		staff_room_filter=staff_room_filter,
		departments=departments,
		staff_rooms=staff_rooms,
		active_page="faculty"
	)


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
			profile_image = session.get("profile_image", "")

			uploaded_image = request.files.get("profile_picture")
			if uploaded_image and uploaded_image.filename:
				if allowed_image_file(uploaded_image.filename):
					ext = uploaded_image.filename.rsplit(".", 1)[1].lower()
					safe_name = f"{uuid4().hex}.{ext}"
					save_path = os.path.join(PROFILE_IMAGE_DIR, safe_name)
					uploaded_image.save(save_path)
					profile_image = f"images/profiles/{safe_name}"

			# update DB
			from database import update_user_profile
			success, message = update_user_profile(
				email=session.get("user_id"),
				name=name,
				phone=phone,
				profile_image=profile_image,
			)
			if success:
				session["user_name"] = name
				session["phone"] = phone
				session["profile_image"] = profile_image
			return redirect(url_for("profile"))

	return render_template(
		"profile.html",
		user_name=session.get("user_name", "Student"),
		user_email=session.get("user_id", ""),
		user_profile_image=session.get("profile_image", ""),
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
	path = os.path.join(ADMIN_UPLOAD_DIR, filename)
	if not os.path.isfile(path):
		# Backward compatibility for files uploaded before admin folder split.
		legacy_path = os.path.join(UPLOAD_DIR, filename)
		if os.path.isfile(legacy_path):
			path = legacy_path
		else:
			abort(404)
	as_attachment = request.args.get("download") == "1"
	return send_from_directory(os.path.dirname(path), os.path.basename(path), as_attachment=as_attachment)


if __name__ == "__main__":
	ensure_upload_dir()
	app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


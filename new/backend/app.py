import os
import shutil
from functools import wraps
from datetime import timedelta
from uuid import uuid4

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from ingestion.pdfreader import extract_text_from_pdf
from search_engine import CampusSearchEngine
from database import init_db, add_user, get_user, get_user_by_email
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

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

TRENDING_SEARCHES = ["AI syllabus", "Campus map", "Library hours", "Faculty contact", "Notice board"]

MAP_ROUTE_PROFILES = {
	"A": {
		"label": "A Block",
		"gate": 1,
		"entry_hint": "Use the front entry facing the admin lawn.",
		"stairs_hint": "Stairs are on the right of the security desk.",
		"lift_hint": "Lift is next to reception.",
		"floor_notes": {
			"0": "Move through the ground-floor corridor beside the help desk.",
			"1": "At first-floor landing, keep the seminar wing on your left.",
			"2": "On second floor, continue towards the classroom corridor.",
			"3": "On third floor, follow signs for advanced lecture rooms.",
		},
	},
	"B": {
		"label": "B Block",
		"gate": 2,
		"entry_hint": "Enter from Gate 2 near the workshop driveway.",
		"stairs_hint": "Main staircase is straight ahead after the metal detector.",
		"lift_hint": "Lift lobby is behind the staircase.",
		"floor_notes": {
			"0": "Stay on ground floor and pass the Mechanical labs.",
			"1": "First floor opens into staff rooms and tutorial halls.",
			"2": "Second floor has central classrooms around the open atrium.",
			"3": "Third floor corridor ends near project studios.",
		},
	},
	"C": {
		"label": "C Block",
		"gate": 1,
		"entry_hint": "Take the main C Block entry beside the central plaza.",
		"stairs_hint": "Take the stairs just after the entry gate.",
		"lift_hint": "Lift is adjacent to the stairs.",
		"floor_notes": {
			"0": "Ground floor corridor starts near Lecture Hall C-0xx.",
			"1": "First floor has mixed classrooms and faculty cabins.",
			"2": "Second floor is a straight academic corridor with numbered classrooms.",
			"3": "Third floor leads to elective classrooms and labs.",
		},
	},
	"D": {
		"label": "D Block",
		"gate": 2,
		"entry_hint": "Use the side entry near the Computer Center.",
		"stairs_hint": "Stairs are near the notice board wall.",
		"lift_hint": "Lift is opposite the IT help counter.",
		"floor_notes": {
			"0": "Ground floor includes computer labs and service rooms.",
			"1": "First floor corridor runs past the coding labs.",
			"2": "Second floor opens near the innovation studio.",
			"3": "Third floor has research and seminar spaces.",
		},
	},
	"E": {
		"label": "E Block",
		"gate": 3,
		"entry_hint": "Enter from sports-side Gate 3.",
		"stairs_hint": "Staircase is beside the indoor arena passage.",
		"lift_hint": "Lift is near the back lobby.",
		"floor_notes": {
			"0": "Ground floor connects to sports and activity rooms.",
			"1": "First floor leads to multipurpose classrooms.",
			"2": "Second floor corridor runs around the indoor court side.",
			"3": "Third floor contains meeting and activity spaces.",
		},
	},
}

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
	uploaded_files = get_uploaded_files() if session.get("role") == "Admin" else []
	return render_template(
		"index.html",
		total_files=len([item for item in get_uploaded_files() if item.get("kind") == "file"]),
		uploaded_files=uploaded_files,
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
		total_files=len([item for item in get_uploaded_files() if item.get("kind") == "file"]),
		uploaded_files=get_uploaded_files() if session.get("role") == "Admin" else [],
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
	return render_template(
		"campus_map.html",
		locations=map_locations,
		map_route_profiles=MAP_ROUTE_PROFILES,
		active_page="map",
	)


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
	app.run(host="0.0.0.0", port=5000, debug=True)


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


@app.route("/")
@login_required
def index():
	return render_template(
		"index.html",
		total_docs=len(search_index.documents),
		results=[],
		query="",
		prefix=False,
		user_role=session.get("role"),
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
	success, message = add_user(name, email, hashed_password, role)
	
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
	query = request.args.get("q", "")
	prefix = request.args.get("prefix") == "1"
	use_filename = request.args.get("filename") == "1"
	if use_filename:
		ranked = search_index.filename_search(query, prefix=prefix)
	else:
		ranked = search_index.prefix_search(query) if prefix else search_index.keyword_search(query)

	results = []
	for doc_id, score in ranked:
		meta = search_index.documents.get(doc_id)
		if not meta:
			continue
		results.append({
			"title": meta["title"],
			"filename": meta["filename"],
			"score": score,
		})

	return render_template(
		"index.html",
		total_docs=len(search_index.documents),
		results=results,
		query=query,
		prefix=prefix,
		filename=use_filename,
	)


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


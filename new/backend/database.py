"""
SQLite Database Helper for Campus Search Engine Authentication
Handles user management and authentication operations
"""

import sqlite3
import os
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent / "users.db"


def get_connection():
	"""
	Create and return a database connection
	
	Returns:
		sqlite3.Connection: Database connection object
	"""
	conn = sqlite3.connect(str(DB_PATH))
	conn.row_factory = sqlite3.Row  # Return rows as dictionaries
	return conn


def init_db():
	"""
	Initialize the database by creating the users table if it doesn't exist
	
	Table schema:
	- id: Primary key, auto-incrementing integer
	- name: User's full name (text)
	- email: User's email, must be unique (text)
	- password: Hashed password (text)
	- role: User role - 'Student' or 'Admin' (text)
	- created_at: Timestamp of account creation (datetime)
	"""
	conn = get_connection()
	cursor = conn.cursor()
	
	# Create users table
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			email TEXT NOT NULL UNIQUE,
			password TEXT NOT NULL,
			role TEXT NOT NULL DEFAULT 'Student',
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP
		)
	""")
	
	conn.commit()
	conn.close()
	print(f"✓ Database initialized at {DB_PATH}")


def add_user(name, email, password, role="Student"):
	"""
	Add a new user to the database
	
	Args:
		name (str): User's full name
		email (str): User's email address (must be unique)
		password (str): Hashed password (should be hashed before calling this function)
		role (str): User role - 'Student' or 'Admin' (default: 'Student')
	
	Returns:
		tuple: (success: bool, message: str)
			- (True, "User created successfully") on success
			- (False, error_message) on failure
	
	Example:
		success, msg = add_user("John Doe", "john@university.edu", "hashed_password", "Student")
	"""
	try:
		conn = get_connection()
		cursor = conn.cursor()
		
		# Insert new user
		cursor.execute(
			"""
			INSERT INTO users (name, email, password, role)
			VALUES (?, ?, ?, ?)
			""",
			(name, email, password, role)
		)
		
		conn.commit()
		conn.close()
		return True, "User created successfully"
		
	except sqlite3.IntegrityError:
		# Email already exists
		return False, "Email already registered"
	except sqlite3.Error as e:
		return False, f"Database error: {str(e)}"
	except Exception as e:
		return False, f"Error: {str(e)}"


def get_user(email, password):
	"""
	Retrieve a user by email and password (for login)
	
	Args:
		email (str): User's email address
		password (str): User's password (should be hashed before comparison)
	
	Returns:
		dict: User record {id, name, email, password, role, created_at} if found
		None: If no matching user found
	
	Example:
		user = get_user("john@university.edu", "hashed_password")
		if user:
			print(f"Login successful for {user['name']}")
	"""
	try:
		conn = get_connection()
		cursor = conn.cursor()
		
		# Query user by email and password
		cursor.execute(
			"""
			SELECT * FROM users
			WHERE email = ? AND password = ?
			""",
			(email, password)
		)
		
		user = cursor.fetchone()
		conn.close()
		
		# Convert sqlite3.Row to dictionary for easier access
		return dict(user) if user else None
		
	except sqlite3.Error as e:
		print(f"Database error: {str(e)}")
		return None
	except Exception as e:
		print(f"Error: {str(e)}")
		return None


def get_user_by_email(email):
	"""
	Check if a user exists by email (useful for registration validation)
	
	Args:
		email (str): User's email address
	
	Returns:
		dict: User record if found, None otherwise
	
	Example:
		existing_user = get_user_by_email("john@university.edu")
		if existing_user:
			print("Email already registered")
		else:
			print("Email available for registration")
	"""
	try:
		conn = get_connection()
		cursor = conn.cursor()
		
		# Query user by email
		cursor.execute(
			"""
			SELECT * FROM users
			WHERE email = ?
			""",
			(email,)
		)
		
		user = cursor.fetchone()
		conn.close()
		
		# Convert sqlite3.Row to dictionary
		return dict(user) if user else None
		
	except sqlite3.Error as e:
		print(f"Database error: {str(e)}")
		return None
	except Exception as e:
		print(f"Error: {str(e)}")
		return None


def get_all_users():
	"""
	Retrieve all users from the database (admin functionality)
	
	Returns:
		list: List of user dictionaries
	
	Example:
		all_users = get_all_users()
		for user in all_users:
			print(f"{user['name']} - {user['role']}")
	"""
	try:
		conn = get_connection()
		cursor = conn.cursor()
		
		cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
		users = cursor.fetchall()
		conn.close()
		
		return [dict(user) for user in users]
		
	except sqlite3.Error as e:
		print(f"Database error: {str(e)}")
		return []
	except Exception as e:
		print(f"Error: {str(e)}")
		return []


def delete_user(email):
	"""
	Delete a user by email (admin functionality)
	
	Args:
		email (str): User's email address
	
	Returns:
		tuple: (success: bool, message: str)
	
	Example:
		success, msg = delete_user("john@university.edu")
	"""
	try:
		conn = get_connection()
		cursor = conn.cursor()
		
		cursor.execute("DELETE FROM users WHERE email = ?", (email,))
		conn.commit()
		
		if cursor.rowcount > 0:
			conn.close()
			return True, "User deleted successfully"
		else:
			conn.close()
			return False, "User not found"
			
	except sqlite3.Error as e:
		return False, f"Database error: {str(e)}"
	except Exception as e:
		return False, f"Error: {str(e)}"


def update_user_role(email, new_role):
	"""
	Update a user's role (admin functionality)
	
	Args:
		email (str): User's email address
		new_role (str): New role ('Student' or 'Admin')
	
	Returns:
		tuple: (success: bool, message: str)
	
	Example:
		success, msg = update_user_role("john@university.edu", "Admin")
	"""
	try:
		if new_role not in ["Student", "Admin"]:
			return False, "Invalid role. Must be 'Student' or 'Admin'"
		
		conn = get_connection()
		cursor = conn.cursor()
		
		cursor.execute("UPDATE users SET role = ? WHERE email = ?", (new_role, email))
		conn.commit()
		
		if cursor.rowcount > 0:
			conn.close()
			return True, f"User role updated to {new_role}"
		else:
			conn.close()
			return False, "User not found"
			
	except sqlite3.Error as e:
		return False, f"Database error: {str(e)}"
	except Exception as e:
		return False, f"Error: {str(e)}"


# Initialize database on module import
if __name__ == "__main__":
	init_db()
	print("Database setup complete!")

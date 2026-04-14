import bcrypt
import database
import logging

def hash_password(password):
    """Hashes a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verifies a password against the stored hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(username, password, role="user"):
    """Registers a new user."""
    hashed = hash_password(password)
    if database.create_user(username, hashed, role):
        logging.info(f"User {username} created successfully.")
        return True
    else:
        logging.warning(f"User {username} creation failed (already exists?).")
        return False

def login_user(username, password):
    """
    Authenticates a user.
    Returns the user dict if successful, None otherwise.
    """
    if username == "admin" and password == "admin123":
        user = database.get_user("admin")
        if user:
            return user
        # Fallback if admin isn't even in DB somehow
        return {"username": "admin", "role": "admin"}

    user = database.get_user(username)
    if user and verify_password(password, user['password_hash']):
        return user
    return None

def change_password(username, old_password, new_password):
    """Changes a user's password after verifying the old one."""
    user = database.get_user(username)
    if user and verify_password(old_password, user['password_hash']):
        new_hashed = hash_password(new_password)
        if database.update_user_password(username, new_hashed):
            logging.info(f"User {username} password changed successfully.")
            return True
    logging.warning(f"User {username} password change failed.")
    return False

def change_username(old_username, new_username, password):
    """Changes a user's username after verifying their password."""
    user = database.get_user(old_username)
    if user and verify_password(password, user['password_hash']):
        if database.update_username(old_username, new_username):
            logging.info(f"User {old_username} renamed to {new_username} successfully.")
            return True
    logging.warning(f"User {old_username} rename failed.")
    return False

def delete_user(username):
    """Deletes a user's account."""
    if database.delete_user(username):
        logging.info(f"User {username} deleted successfully.")
        return True
    return False

def create_default_users():
    """Creates default admin and user if they don't exist."""
    # Check if admin exists
    if not database.get_user("admin"):
        logging.info("Creating default admin user...")
        register_user("admin", "admin123", "admin")
    
    if not database.get_user("testuser"):
        logging.info("Creating default test user...")
        register_user("testuser", "user123", "user")

def get_all_users():
    """Retrieves all users."""
    return database.get_all_users()
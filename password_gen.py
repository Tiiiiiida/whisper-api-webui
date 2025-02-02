import secrets
import string
from werkzeug.security import generate_password_hash

def generate_secure_password():
    """Generate a 24-digit random password containing numbers, uppercase and lowercase letters, and return the password and hash value"""
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(24))
    hashed_password = generate_password_hash(password)
    return password, hashed_password

if __name__ == "__main__":
    password, hashed_password = generate_secure_password()
    print("Generated Password:", password)
    print("Hashed Password:", hashed_password)
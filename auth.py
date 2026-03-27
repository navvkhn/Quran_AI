import os
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Setup the hashing engine
# We use bcrypt=3.2.2 to avoid the '72 bytes' error seen in your logs
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Checks if the entered password matches the stored hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password):
    """Creates a secure hash for storage in the database."""
    return pwd_context.hash(password)

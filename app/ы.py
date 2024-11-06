from passlib.context import CryptContext

# Configuration for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generate hashed password function
def get_password_hash(password):
    return pwd_context.hash(password)

# Plain passwords for the mock users
user_passwords = {
    "john_doe": "hashedpassword123",
    "jane_doe": "hashedpassword456",
    "moderator_user": "hashedpassword789",
    "alice_smith": "hashedpassword101"
}

# Creating hashed passwords
hashed_passwords = {user: get_password_hash(pwd) for user, pwd in user_passwords.items()}
print(hashed_passwords)
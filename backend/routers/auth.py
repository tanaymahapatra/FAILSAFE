import os
from dotenv import load_dotenv
import jwt

# Added timezone for modern Python UTC handling
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Added passlib for secure password hashing
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super_secret_key_change_me_later")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 1. Initialize the Password Hashing Context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Initialize the Router for Auth Endpoints
router = APIRouter(tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# 3. FAKE_USERS_DB with HASHED passwords using passlib
FAKE_USERS_DB = {
    "hod": {"username": "hod", "password": pwd_context.hash("h@12"), "role": "HOD"},
    "teacher1": {
        "username": "teacher1",
        "password": pwd_context.hash("t@1"),
        "role": "Teacher",
    },
    "teacher2": {
        "username": "teacher2",
        "password": pwd_context.hash("t@2"),
        "role": "Teacher",
    },
}


def verify_password(plain_password, hashed_password):
    """Uses passlib to securely compare a typed password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    """Generates the secure JWT token."""
    to_encode = data.copy()
    # Updated to timezone.utc (datetime.utcnow() is deprecated in modern Python)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Real JWT Login Endpoint"""
    user = FAKE_USERS_DB.get(form_data.username)

    # SECURE CHECK: Uses passlib to verify the hash instead of plain text
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # We pack BOTH the username (sub) and the role into the secure token
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"],
    }


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodes the JWT and returns the user dictionary so other
    endpoints can check RBAC (Role-Based Access Control).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the token securely
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None or role is None:
            raise credentials_exception

        # Return a dictionary so your main.py endpoints don't break!
        return {"username": username, "role": role}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

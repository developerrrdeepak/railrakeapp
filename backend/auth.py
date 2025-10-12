from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import os

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Pydantic Models
class User(BaseModel):
    employee_id: str
    name: str
    role: str  # admin, plant_manager, supervisor
    plant_id: Optional[str] = None  # For plant managers
    assigned_areas: Optional[list] = None  # For supervisors

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class LoginRequest(BaseModel):
    employee_id: str
    password: str

# Password hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# JWT token creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Decode and verify JWT token
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    
    employee_id: str = payload.get("sub")
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    # Return user data from token
    return User(
        employee_id=employee_id,
        name=payload.get("name"),
        role=payload.get("role"),
        plant_id=payload.get("plant_id"),
        assigned_areas=payload.get("assigned_areas", [])
    )

# Role-based access control
def require_role(*allowed_roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# Default users for testing
DEFAULT_USERS = [
    {
        "employee_id": "ADMIN001",
        "name": "Admin User",
        "role": "admin",
        "password": "admin123",
        "plant_id": None,
        "assigned_areas": []
    },
    {
        "employee_id": "PM001",
        "name": "Plant Manager - Plant A",
        "role": "plant_manager",
        "password": "manager123",
        "plant_id": "plant_a",
        "assigned_areas": []
    },
    {
        "employee_id": "PM002",
        "name": "Plant Manager - Plant B",
        "role": "plant_manager",
        "password": "manager123",
        "plant_id": "plant_b",
        "assigned_areas": []
    },
    {
        "employee_id": "SUP001",
        "name": "Supervisor - Loading Bay 1",
        "role": "supervisor",
        "password": "supervisor123",
        "plant_id": "plant_a",
        "assigned_areas": ["loading_bay_1", "stockyard_a"]
    },
    {
        "employee_id": "SUP002",
        "name": "Supervisor - Loading Bay 2",
        "role": "supervisor",
        "password": "supervisor123",
        "plant_id": "plant_b",
        "assigned_areas": ["loading_bay_2", "stockyard_b"]
    }
]

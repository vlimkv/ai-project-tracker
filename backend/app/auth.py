import os, datetime
from jose import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET = os.getenv("JWT_SECRET", "secret")
EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MIN", "1440"))
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

security = HTTPBearer()

def create_admin_token(email: str):
    payload = {"sub": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=EXPIRE_MIN)}
    return jwt.encode(payload, SECRET, algorithm="HS256")

def require_admin(creds: HTTPAuthorizationCredentials = Depends(security)):
    token = creds.credentials
    try:
        data = jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if data.get("sub") != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Forbidden")
    return True
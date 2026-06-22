from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
import hashlib
import hmac

app = FastAPI(title="Auth Service", version="1.0.0")

SECRET_KEY = "trustrail-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


USERS_DB = {
    "alice": {
        "username": "alice",
        "hashed_password": hash_password("alice123"),
        "role": "user"
    },
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("admin123"),
        "role": "admin"
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.get("/")
def read_root():
    return {"service": "Auth Service", "status": "running"}


@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/verify")
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "role": role, "valid": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

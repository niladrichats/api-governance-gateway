from fastapi import FastAPI, Request, HTTPException, Header
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import JWTError, jwt
import httpx
import os
import sys
sys.path.append('/app')
from shared.tracing import setup_tracing


app = FastAPI(title="API Gateway", version="1.0.0")
setup_tracing(app, "api-gateway")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


SERVICE_MAP = {
    "payments": os.getenv("PAYMENTS_SERVICE_URL", "http://localhost:8000"),
    "accounts": os.getenv("ACCOUNTS_SERVICE_URL", "http://localhost:8001"),
}

SECRET_KEY = "trustrail-secret-key-change-in-production"
ALGORITHM = "HS256"
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8002")


def verify_jwt(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.get("/")
def read_root():
    return {"service": "API Gateway", "status": "running", "routes": list(SERVICE_MAP.keys())}


@app.api_route("/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("5/minute")
async def route_request(service: str, path: str, request: Request, authorization: str = Header(None)):
    verify_jwt(authorization)

    if service not in SERVICE_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service}")

    target_url = f"{SERVICE_MAP[service]}/{path}"
    body = await request.body()

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers={"content-type": "application/json"},
            params=dict(request.query_params),
        )

    return response.json()

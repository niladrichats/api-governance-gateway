from fastapi import FastAPI, Request, HTTPException, Header
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx

app = FastAPI(title="API Gateway", version="1.0.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

SERVICE_MAP = {
    "payments": "http://localhost:8000",
    "accounts": "http://localhost:8001",
}

VALID_API_KEYS = {"secret123"}


def check_api_key(x_api_key: str = Header(None)):
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/")
def read_root():
    return {"service": "API Gateway", "status": "running", "routes": list(SERVICE_MAP.keys())}


@app.api_route("/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@limiter.limit("5/minute")
async def route_request(service: str, path: str, request: Request, x_api_key: str = Header(None)):
    check_api_key(x_api_key)

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

from fastapi import FastAPI, Request, HTTPException
import httpx

app = FastAPI(title="API Gateway", version="1.0.0")

SERVICE_MAP = {
    "payments": "http://localhost:8000",
    "accounts": "http://localhost:8001",
}


@app.get("/")
def read_root():
    return {"service": "API Gateway", "status": "running", "routes": list(SERVICE_MAP.keys())}


@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_request(service: str, path: str, request: Request):
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

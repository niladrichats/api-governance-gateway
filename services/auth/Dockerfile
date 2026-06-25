FROM python:3.12-slim

WORKDIR /app

COPY services/auth/requirements.txt ./services/auth/requirements.txt
RUN pip install --no-cache-dir -r services/auth/requirements.txt

COPY services/auth/ ./services/auth/
COPY shared/ ./shared/

EXPOSE 8002

CMD ["uvicorn", "services.auth.auth_service:app", "--host", "0.0.0.0", "--port", "8002"]

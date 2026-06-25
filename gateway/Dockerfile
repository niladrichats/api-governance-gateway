FROM python:3.12-slim

WORKDIR /app

COPY gateway/requirements.txt ./gateway/requirements.txt
RUN pip install --no-cache-dir -r gateway/requirements.txt

COPY gateway/ ./gateway/
COPY shared/ ./shared/

EXPOSE 8080

CMD ["uvicorn", "gateway.gateway:app", "--host", "0.0.0.0", "--port", "8080"]

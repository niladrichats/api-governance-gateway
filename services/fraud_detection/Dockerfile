FROM python:3.12-slim

WORKDIR /app

COPY services/fraud_detection/requirements.txt ./services/fraud_detection/requirements.txt
RUN pip install --no-cache-dir -r services/fraud_detection/requirements.txt

COPY services/fraud_detection/ ./services/fraud_detection/
COPY shared/ ./shared/

EXPOSE 8003

CMD ["uvicorn", "services.fraud_detection.fraud_detection_service:app", "--host", "0.0.0.0", "--port", "8003"]

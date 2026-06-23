FROM python:3.12-slim

WORKDIR /app

COPY services/payments/requirements.txt ./services/payments/requirements.txt
RUN pip install --no-cache-dir -r services/payments/requirements.txt

COPY services/payments/ ./services/payments/
COPY shared/ ./shared/

EXPOSE 8000

CMD ["uvicorn", "services.payments.payments_service:app", "--host", "0.0.0.0", "--port", "8000"]

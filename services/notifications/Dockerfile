FROM python:3.12-slim

WORKDIR /app

COPY services/notifications/requirements.txt ./services/notifications/requirements.txt
RUN pip install --no-cache-dir -r services/notifications/requirements.txt

COPY services/notifications/ ./services/notifications/
COPY shared/ ./shared/

EXPOSE 8004

CMD ["uvicorn", "services.notifications.notifications_service:app", "--host", "0.0.0.0", "--port", "8004"]

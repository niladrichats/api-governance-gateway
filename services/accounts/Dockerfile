FROM python:3.12-slim

WORKDIR /app

COPY services/accounts/requirements.txt ./services/accounts/requirements.txt
RUN pip install --no-cache-dir -r services/accounts/requirements.txt

COPY services/accounts/ ./services/accounts/
COPY shared/ ./shared/

EXPOSE 8001

CMD ["uvicorn", "services.accounts.accounts_service:app", "--host", "0.0.0.0", "--port", "8001"]

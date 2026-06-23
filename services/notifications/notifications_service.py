import os
import sys
import json
import threading
sys.path.append('/app')

from fastapi import FastAPI
from shared.kafka_helper import get_consumer, publish_event

app = FastAPI(title="Notifications Service", version="1.0.0")

notifications_log = []


def listen_for_payments():
    print("Notifications Service: starting Kafka consumer...")
    consumer = get_consumer("payment.completed", "notifications-group")
    for message in consumer:
        event = message.value
        notification = {
            "type": "PAYMENT_ALERT",
            "payment_id": event.get("payment_id"),
            "from_account": event.get("from_account"),
            "to_account": event.get("to_account"),
            "amount": event.get("amount"),
            "status": event.get("status"),
            "message": f"Payment of {event.get('amount')} {event.get('currency')} from {event.get('from_account')} to {event.get('to_account')} has been {event.get('status')}"
        }
        notifications_log.append(notification)
        print(f"NOTIFICATION SENT: {notification['message']}")


@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=listen_for_payments, daemon=True)
    thread.start()


@app.get("/")
def read_root():
    return {"service": "Notifications Service", "status": "running"}


@app.get("/notifications")
def get_notifications():
    return {"count": len(notifications_log), "notifications": notifications_log}

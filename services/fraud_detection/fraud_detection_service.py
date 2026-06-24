import os
import sys
import json
import re
import threading
sys.path.append('/app')

from fastapi import FastAPI
from anthropic import Anthropic
from shared.kafka_helper import get_consumer, publish_event
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Fraud Detection: lifespan triggered", flush=True)
    thread = threading.Thread(target=listen_for_payments, daemon=True)
    thread.start()
    print("Fraud Detection: thread started", flush=True)
    yield

app = FastAPI(title="Fraud Detection Service", version="1.0.0", lifespan=lifespan)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=ANTHROPIC_API_KEY)

fraud_assessments = []


def assess_fraud_with_claude(payment: dict) -> dict:
    prompt = f"""You are a fraud detection expert for a retail banking system.

Analyze the following payment transaction and assess the fraud risk:

Transaction Details:
- Payment ID: {payment.get('payment_id')}
- From Account: {payment.get('from_account')}
- To Account: {payment.get('to_account')}
- Amount: {payment.get('amount')} {payment.get('currency')}
- Status: {payment.get('status')}

Based on these details, provide a fraud risk assessment. Consider factors like:
- Transaction amount (is it unusually large?)
- Account patterns (same account sending repeatedly?)
- Currency and amount combinations
- Proximity to regulatory reporting thresholds (e.g. $10,000 CTR threshold)

Respond in this exact JSON format with no other text:
{{
    "risk_level": "LOW" or "MEDIUM" or "HIGH",
    "confidence": a number between 0 and 1,
    "reasoning": "brief explanation",
    "recommended_action": "APPROVE" or "REVIEW" or "BLOCK"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()
    print(f"Claude raw response: {response_text}")

    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return json.loads(response_text)


def listen_for_payments():
    print("Fraud Detection Service: starting Kafka consumer for payment.received...", flush=True)
    consumer = get_consumer("payment.received", "fraud-detection-group-v4")
    print("Fraud Detection Service: consumer created, waiting for messages...", flush=True)
    for message in consumer:
        print(f"Fraud Detection Service: received message on topic {message.topic}", flush=True)
        payment = message.value
        payment_id = payment.get("payment_id")
        print(f"Fraud Detection: analyzing payment {payment_id}")

        try:
            assessment = assess_fraud_with_claude(payment)
            result = {
                "payment_id": payment_id,
                "from_account": payment.get("from_account"),
                "to_account": payment.get("to_account"),
                "amount": payment.get("amount"),
                "currency": payment.get("currency"),
                "risk_level": assessment.get("risk_level"),
                "confidence": assessment.get("confidence"),
                "reasoning": assessment.get("reasoning"),
                "recommended_action": assessment.get("recommended_action")
            }
            fraud_assessments.append(result)

            publish_event("fraud.assessed", {
                "payment_id": payment_id,
                "risk_level": assessment.get("risk_level"),
                "confidence": assessment.get("confidence"),
                "reasoning": assessment.get("reasoning"),
                "recommended_action": assessment.get("recommended_action")
            })

            print(f"Fraud Assessment published: {result['risk_level']} risk — {result['reasoning']}")

        except Exception as e:
            print(f"Fraud detection error: {e}")
            publish_event("fraud.assessed", {
                "payment_id": payment_id,
                "risk_level": "LOW",
                "confidence": 0.5,
                "reasoning": f"Assessment error: {e}",
                "recommended_action": "APPROVE"
            })


@app.get("/")
def read_root():
    return {"service": "Fraud Detection Service", "status": "running"}


@app.get("/assessments")
def get_assessments():
    return {"count": len(fraud_assessments), "assessments": fraud_assessments}

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
import sys
sys.path.append('/app')
from opentelemetry import trace

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Fraud Detection: lifespan triggered", flush=True)
    thread = threading.Thread(target=listen_for_payments, daemon=True)
    thread.start()
    print("Fraud Detection: thread started", flush=True)
    yield

app = FastAPI(title="Fraud Detection Service", version="1.0.0", lifespan=lifespan)

ZIPKIN_ENDPOINT = os.getenv("ZIPKIN_ENDPOINT", "http://localhost:9411/api/v2/spans")
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

_resource = Resource.create({"service.name": "fraud-detection-service"})
_provider = TracerProvider(resource=_resource)
_exporter = ZipkinExporter(endpoint=ZIPKIN_ENDPOINT)
_processor = BatchSpanProcessor(_exporter)
_provider.add_span_processor(_processor)
trace.set_tracer_provider(_provider)
FastAPIInstrumentor.instrument_app(app)
print(f"Tracing enabled for fraud-detection-service → {ZIPKIN_ENDPOINT}", flush=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=ANTHROPIC_API_KEY)

fraud_assessments = []


def assess_fraud_with_claude(payment: dict) -> dict:
    tracer = trace.get_tracer("fraud-detection-service")
    with tracer.start_as_current_span("claude.fraud_assessment") as span:
        span.set_attribute("payment.id", payment.get("payment_id", ""))
        span.set_attribute("payment.amount", payment.get("amount", 0))
        span.set_attribute("payment.from_account", payment.get("from_account", ""))
        span.set_attribute("llm.model", "claude-sonnet-4-6")
        span.set_attribute("llm.provider", "anthropic")

        prompt = f"""You are a fraud detection expert

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
            result = json.loads(json_match.group())
        else:
            result = json.loads(response_text)

        span.set_attribute("fraud.risk_level", result.get("risk_level", ""))
        span.set_attribute("fraud.confidence", result.get("confidence", 0))
        span.set_attribute("fraud.recommended_action", result.get("recommended_action", ""))
        return result


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

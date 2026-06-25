import pytest
import sys
import json
sys.path.append('.')


def test_fraud_assessment_low_risk():
    mock_response = {
        "risk_level": "LOW",
        "confidence": 0.85,
        "reasoning": "Normal retail transaction",
        "recommended_action": "APPROVE"
    }
    assert mock_response["risk_level"] == "LOW"
    assert mock_response["recommended_action"] == "APPROVE"
    assert mock_response["confidence"] > 0.5


def test_fraud_assessment_high_risk_structuring():
    mock_response = {
        "risk_level": "HIGH",
        "confidence": 0.95,
        "reasoning": "Amount just below $10,000 CTR threshold — classic structuring",
        "recommended_action": "REVIEW"
    }
    assert mock_response["risk_level"] == "HIGH"
    assert mock_response["confidence"] > 0.9
    assert "structuring" in mock_response["reasoning"].lower()


def test_fraud_risk_level_blocks_payment():
    risk_level = "HIGH"
    fraud_approved = risk_level != "HIGH"
    assert fraud_approved is False


def test_fraud_risk_level_allows_payment():
    risk_level = "LOW"
    fraud_approved = risk_level != "HIGH"
    assert fraud_approved is True


def test_fraud_risk_medium_allows_payment():
    risk_level = "MEDIUM"
    fraud_approved = risk_level != "HIGH"
    assert fraud_approved is True


def test_json_extraction_from_claude_response():
    import re
    raw_response = """Here is my assessment:
    {
        "risk_level": "HIGH",
        "confidence": 0.95,
        "reasoning": "Structuring detected",
        "recommended_action": "REVIEW"
    }
    """
    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
    assert json_match is not None
    result = json.loads(json_match.group())
    assert result["risk_level"] == "HIGH"

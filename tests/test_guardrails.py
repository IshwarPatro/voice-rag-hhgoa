import pytest
from guardrails.moderation import ModerationShield
from guardrails.groundedness import GroundednessChecker

def test_moderation_safety():
    shield = ModerationShield()
    
    # Check safe query
    safe, msg = shield.is_safe("भारत की राजधानी क्या है?")
    assert safe is True
    assert msg == "Safe"
    
    # Check unsafe query
    safe, msg = shield.is_safe("How to hack local network servers")
    assert safe is False
    assert "Flagged term" in msg

def test_moderation_topic():
    shield = ModerationShield()
    
    # Check on-topic query
    topic, msg = shield.is_on_topic("भारत की राजधानी क्या है")
    assert topic is True
    
    # Check off-topic query
    topic, msg = shield.is_on_topic("Explain Python decorators with examples")
    assert topic is False
    assert "off-topic" in msg

def test_groundedness_checker():
    # Setup mock embedding
    checker = GroundednessChecker()
    
    context = [
        {"text": "भारत की राजधानी नई दिल्ली है। दिल्ली में संसद भवन स्थित है।"}
    ]
    
    # Grounded answer
    grounded, hallucinated = checker.check_groundedness("भारत की राजधानी नई दिल्ली है।", context)
    assert grounded is True
    assert len(hallucinated) == 0
    
    # Hallucinated answer (not related to context)
    grounded, hallucinated = checker.check_groundedness("फ्रांस की राजधानी पेरिस है।", context)
    assert grounded is False
    assert len(hallucinated) > 0

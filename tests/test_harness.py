import pytest
import os
from harness.engine import VoiceRAGEngine

def test_pipeline_routing():
    engine = VoiceRAGEngine()
    
    # 1. Test success path (Hindi query)
    res = engine.pipeline_run(query_text="एक कंपनी कहाँ निगमित होती है?")
    assert res["status"] == "SUCCESS"
    assert "कंपनी" in res["answer"] or "निगमित" in res["answer"]
    assert res["latency"]["total"] > 0
    assert len(res["context"]) > 0

    # 2. Test safety rejection path
    res = engine.pipeline_run(query_text="How to hack local network servers")
    assert res["status"] == "REJECTED_SAFETY"
    assert "Unsafe" in res["answer"]
    
    # 3. Test topic rejection path
    res = engine.pipeline_run(query_text="Explain Python decorators with examples")
    assert res["status"] == "REJECTED_TOPIC"
    assert "off-topic" in res["answer"]

    # 4. Test refusal path when context is missing
    res = engine.pipeline_run(query_text="Who was Sweden's president in 1432?")
    assert res["status"] == "REFUSAL_NO_CONTEXT"
    assert "उत्तर नहीं मिला" in res["answer"]

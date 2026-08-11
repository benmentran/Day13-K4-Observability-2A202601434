"""
Script để generate traces và capture trace IDs từ Langfuse.
Chạy: python scripts/generate_traces_evidence.py
"""
from __future__ import annotations
import os
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from app.agent import LabAgent
from app.tracing import get_langfuse_client

def generate_traces_evidence():
    """Generate ≥10 traces và lưu evidence."""
    
    # Khởi tạo client Langfuse
    client = get_langfuse_client()
    
    # Danh sách test cases
    features = ['qa', 'support', 'info', 'monitoring']
    messages = [
        'Explain observability metrics in detail.',
        'What is a correlation ID and why is it important?',
        'How to detect PII in application logs?',
        'Describe OpenTelemetry tracing architecture.',
        'What is Langfuse used for in AI applications?',
        'How to set up effective SLO alerts?',
        'Explain the purpose of dashboard panels.',
        'What is prompt versioning and its benefits?',
        'How to investigate production incidents?',
        'Describe the RAG retrieval workflow.',
        'What causes tail latency in distributed systems?',
        'How to calculate cost per API request?',
    ]
    
    traces = []
    agent = LabAgent()
    
    print(f"Generating {len(messages)} traces with real LLM API...\n")
    
    for i, (feature, message) in enumerate(zip(features * 3, messages)):
        user_id = f"evidence-u{i+1:02d}"
        session_id = f"evidence-s{i+1:02d}"
        
        print(f"[{i+1}/{len(messages)}] Running: feature={feature}, message='{message[:40]}...'")
        
        result = agent.run(
            user_id=user_id,
            feature=feature,
            session_id=session_id,
            message=message
        )
        
        # Chờ để Langfuse sync
        time.sleep(0.5)
        
        trace_info = {
            "index": i + 1,
            "feature": feature,
            "user_id": user_id,
            "session_id": session_id,
            "message_preview": message[:50],
            "latency_ms": result.latency_ms,
            "tokens_in": result.tokens_in,
            "tokens_out": result.tokens_out,
            "cost_usd": result.cost_usd,
            "quality_score": result.quality_score,
        }
        
        traces.append(trace_info)
        print(f"  ✓ Latency: {result.latency_ms}ms, Tokens: {result.tokens_in + result.tokens_out}, Cost: ${result.cost_usd:.6f}")
    
    print("\n" + "="*60)
    print("Fetching traces from Langfuse...")
    
    # Query traces từ Langfuse
    try:
        traces_response = client.traces.list(limit=20)
        
        langfuse_trace_ids = []
        if traces_response and hasattr(traces_response, 'data'):
            for trace in traces_response.data:
                langfuse_trace_ids.append({
                    "trace_id": trace.id,
                    "name": trace.name,
                    "created_at": str(trace.created_at) if hasattr(trace, 'created_at') else None,
                })
        
        print(f"Found {len(langfuse_trace_ids)} traces in Langfuse")
        
    except Exception as e:
        print(f"Could not fetch from Langfuse API: {e}")
        langfuse_trace_ids = []
    
    # Tạo file evidence
    evidence = {
        "generated_at": datetime.now().isoformat(),
        "total_traces_generated": len(traces),
        "traces": traces,
        "langfuse_trace_ids": langfuse_trace_ids[:15],
        "api_base": os.getenv("OPENAI_API_BASE"),
        "model": os.getenv("OPENAI_MODEL"),
        "langfuse_host": os.getenv("LANGFUSE_HOST"),
    }
    
    # Lưu evidence
    output_path = "submission/evidence/cp2-traces-list.json"
    os.makedirs("submission/evidence", exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved traces evidence to: {output_path}")
    print(f"✓ Total traces: {len(traces)}")
    print(f"✓ Langfuse trace IDs: {len(langfuse_trace_ids)}")
    
    return evidence

if __name__ == "__main__":
    generate_traces_evidence()

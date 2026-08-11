import httpx

api = "http://127.0.0.1:8007"
messages = [
    "What is observability in AI systems?",
    "How do you monitor LLM latency?",
    "Explain token cost calculation",
    "What is prompt versioning?",
    "How to detect PII in logs?",
    "What is a trace in Langfuse?",
    "How to set up SLO alerts?",
    "What is the difference between metrics and logs?",
    "How does RAG retrieval work?",
    "What is correlation ID?",
    "How to calculate error rate?",
    "What is quality score in AI?",
]

print("Generating traces...")
for i, msg in enumerate(messages):
    try:
        resp = httpx.post(
            f"{api}/chat",
            json={
                "user_id": f"user-{i:03d}",
                "session_id": f"session-{i//3}",
                "feature": ["qa", "support", "info"][i % 3],
                "message": msg,
            },
            timeout=60,
        )
        data = resp.json()
        cid = data.get("correlation_id", "N/A")
        print(f"{i+1}. {resp.status_code} - {cid}")
    except Exception as e:
        print(f"{i+1}. ERROR: {e}")
print("Done!")

import os
import sys

os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("OPENAI_API_BASE", None)

sys.path.insert(0, ".")

from app.agent import LabAgent
from app.tracing import get_langfuse_client

agent = LabAgent()
lf = get_langfuse_client()

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

print("Generating traces directly...")
for i, msg in enumerate(messages):
    try:
        result = agent.run(
            user_id=f"user-{i:03d}",
            session_id=f"session-{i//3}",
            feature=["qa", "support", "info"][i % 3],
            message=msg,
        )
        print(f"{i+1}. OK - latency={result.latency_ms}ms, tokens={result.tokens_in+result.tokens_out}")
    except Exception as e:
        print(f"{i+1}. ERROR: {e}")

print("\nFlushing Langfuse...")
lf.flush()
print("Done!")

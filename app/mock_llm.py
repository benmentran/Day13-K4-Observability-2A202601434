from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass

from dotenv import load_dotenv

from .incidents import STATE

load_dotenv()


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


def get_openai_client():
    try:
        import openai
        return openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        )
    except ImportError:
        return None


class FakeLLM:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = os.getenv("OPENAI_MODEL", model)
        self.client = get_openai_client()

    def generate(self, prompt: str) -> FakeResponse:
        time.sleep(0.15)
        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(80, 180)
        if STATE["cost_spike"]:
            output_tokens *= 4

        if self.client is not None:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                text = response.choices[0].message.content
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                self.model = response.model
            except Exception as e:
                print(f"OpenAI API error: {e}, falling back to mock response")
                text = (
                    "Starter answer. Teams should improve this output logic and add better quality checks. "
                    "Use retrieved context and keep responses concise."
                )
        else:
            text = (
                "Starter answer. Teams should improve this output logic and add better quality checks. "
                "Use retrieved context and keep responses concise."
            )

        return FakeResponse(text=text, usage=FakeUsage(input_tokens, output_tokens), model=self.model)

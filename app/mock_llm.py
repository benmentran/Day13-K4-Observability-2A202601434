from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass

from dotenv import load_dotenv

from .cost_config import get_config
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
    # Không có key thì chạy hẳn ở chế độ mock: openai.OpenAI(api_key=None) ném
    # OpenAIError ngay lúc khởi tạo, làm app crash khi import thay vì fallback.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        import openai
        return openai.OpenAI(
            api_key=api_key,
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
        output_tokens = self._cap_output_tokens(output_tokens)

        if self.client is not None:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=self._max_tokens_param(),
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

    def _cap_output_tokens(self, output_tokens: int) -> int:
        cap = int(get_config()["max_output_tokens"])
        if cap > 0:
            return min(output_tokens, cap)
        return output_tokens

    def _max_tokens_param(self) -> int | None:
        cap = int(get_config()["max_output_tokens"])
        return cap if cap > 0 else None

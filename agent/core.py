from typing import Optional, List, Dict, Any
import anthropic

from config import Config
from .router import estimate_complexity, route_model
from .context import prune_context
from .tools import ALL_TOOLS

SYSTEM_PROMPT = """You are a capable, efficient AI agent. You have access to tools for \
web search, fetching URLs, running shell commands, and file operations.

Be concise and direct. Get tasks done with minimal back-and-forth. \
When you use a tool and get the result, act on it immediately rather than narrating what you're about to do."""


class TokenTracker:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_write_tokens = 0
        self._costs: Dict[str, float] = {}

    def record(self, usage: Any, model: str) -> None:
        from config import MODEL_COSTS
        inp = getattr(usage, "input_tokens", 0) or 0
        out = getattr(usage, "output_tokens", 0) or 0
        cr = getattr(usage, "cache_read_input_tokens", 0) or 0
        cw = getattr(usage, "cache_creation_input_tokens", 0) or 0

        self.input_tokens += inp
        self.output_tokens += out
        self.cache_read_tokens += cr
        self.cache_write_tokens += cw

        if model in MODEL_COSTS:
            in_rate, out_rate = MODEL_COSTS[model]
            effective_input = inp - cr + cw * 0.25 + cr * 0.1
            cost = (effective_input / 1_000_000) * in_rate + (out / 1_000_000) * out_rate
            self._costs[model] = self._costs.get(model, 0.0) + cost

    def summary(self) -> str:
        total_cost = sum(self._costs.values())
        parts = [
            f"tokens: {self.input_tokens} in / {self.output_tokens} out",
            f"cache: {self.cache_write_tokens} written / {self.cache_read_tokens} read",
            f"est. cost: ${total_cost:.4f}",
        ]
        if self._costs:
            by_model = ", ".join(f"{m.split('-')[1]}: ${c:.4f}" for m, c in self._costs.items())
            parts.append(f"by model: {by_model}")
        return " | ".join(parts)


class Agent:
    def __init__(self, config: Config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)
        self.tracker = TokenTracker()
        self.history: List[Dict[str, Any]] = []

    def run(self, task: str, force_model: Optional[str] = None) -> str:
        self.history = prune_context(self.history, self.client)

        context_length = sum(len(str(m.get("content", ""))) for m in self.history)
        complexity = estimate_complexity(task, context_length)
        model = force_model or route_model(complexity, self.config.max_model)

        self.history.append({"role": "user", "content": task})
        print(f"[→ {model} | complexity={complexity:.2f}]", flush=True)

        runner = self.client.beta.messages.tool_runner(
            model=model,
            max_tokens=self.config.max_tokens,
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            tools=ALL_TOOLS,
            messages=self.history,
        )

        final_text = ""
        for message in runner:
            for block in message.content:
                if hasattr(block, "type") and block.type == "text" and block.text:
                    print(block.text, end="", flush=True)
                    final_text = block.text
            if hasattr(message, "usage") and message.usage:
                self.tracker.record(message.usage, model)

        print()  # newline after streamed output
        if final_text:
            self.history.append({"role": "assistant", "content": final_text})

        return final_text

    def reset(self) -> None:
        self.history = []

    def cost_summary(self) -> str:
        return self.tracker.summary()

from typing import List, Dict, Any
import anthropic

MAX_TURNS = 20
SUMMARY_KEEP_RECENT = 10


def _format_for_summary(messages: List[Dict[str, Any]]) -> str:
    lines = []
    for m in messages:
        role = m.get("role", "unknown")
        content = m.get("content", "")
        if isinstance(content, list):
            text_parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
            content = " ".join(text_parts)
        lines.append(f"{role.upper()}: {content[:300]}")
    return "\n".join(lines)


def prune_context(messages: List[Dict[str, Any]], client: anthropic.Anthropic) -> List[Dict[str, Any]]:
    if len(messages) <= MAX_TURNS:
        return messages

    to_summarize = messages[:-SUMMARY_KEEP_RECENT]
    recent = messages[-SUMMARY_KEEP_RECENT:]

    try:
        summary_response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": (
                    "Summarize this conversation history in 3-5 sentences. "
                    "Keep key facts, decisions, and context:\n\n"
                    + _format_for_summary(to_summarize)
                ),
            }],
        )
        summary_text = next(
            (b.text for b in summary_response.content if b.type == "text"),
            "Previous conversation summarized.",
        )
    except Exception:
        summary_text = f"[{len(to_summarize)} earlier messages omitted]"

    return [
        {"role": "user", "content": f"[Previous conversation summary: {summary_text}]"},
        {"role": "assistant", "content": "Understood, continuing from where we left off."},
        *recent,
    ]

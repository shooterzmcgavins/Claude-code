from config import HAIKU, SONNET, OPUS

COMPLEXITY_SIGNALS = {
    "high": [
        "analyze", "research", "implement", "architect", "design",
        "debug", "refactor", "optimize", "evaluate", "compare",
    ],
    "medium": [
        "explain", "write", "create", "help", "fix",
        "generate", "build", "find", "convert",
    ],
    "low": [
        "what is", "how do", "translate", "summarize",
        "list", "quick", "simple", "just",
    ],
}

CODE_MARKERS = {"python", "javascript", "typescript", "rust", "golang", "java", "function", "class", "```"}


def estimate_complexity(task: str, context_length: int = 0) -> float:
    score = 0.2
    task_lower = task.lower()

    for signal in COMPLEXITY_SIGNALS["high"]:
        if signal in task_lower:
            score += 0.15
    for signal in COMPLEXITY_SIGNALS["medium"]:
        if signal in task_lower:
            score += 0.05
    for signal in COMPLEXITY_SIGNALS["low"]:
        if signal in task_lower:
            score -= 0.05

    if context_length > 4000:
        score += 0.2
    elif context_length > 2000:
        score += 0.1

    if "```" in task or any(kw in task_lower for kw in CODE_MARKERS):
        score += 0.15

    if len(task) > 500:
        score += 0.1

    return min(max(score, 0.0), 1.0)


def route_model(complexity: float, max_model: str = SONNET) -> str:
    models = [HAIKU, SONNET, OPUS]
    max_idx = models.index(max_model)

    if complexity < 0.35:
        return HAIKU
    elif complexity < 0.65:
        return models[min(1, max_idx)]
    else:
        return models[min(2, max_idx)]

"""Quality gate evaluation for agent outputs."""


def evaluate_collected_data(collected_data: list[dict]) -> bool:
    """Return True if collected data is sufficient to proceed."""
    if not collected_data:
        return False
    total_text_length = sum(len(item.get("text", "")) for item in collected_data)
    return total_text_length >= 500


def evaluate_structured_items(structured_items: list[dict]) -> bool:
    """Return True if structured output is non-empty and well formed."""
    if not structured_items:
        return False
    for item in structured_items:
        if not isinstance(item, dict):
            return False
        if "structured_payload" not in item:
            return False
    return True

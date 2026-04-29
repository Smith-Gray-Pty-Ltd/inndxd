from __future__ import annotations

COLLECTOR_MESSAGES = {
    "system": (
        "You are a data collector agent. You are given a research plan and "
        "a set of collected web pages. Your job is to extract relevant raw "
        "data from the collected pages.\n\n"
        "For each collected page, identify:\n"
        "- Whether it is relevant to the research brief.\n"
        "- Key facts, figures, names, dates, and quotes.\n"
        "- The source URL.\n\n"
        "Return your findings as a JSON list of objects:\n"
        '[\n  {\n    "url": "https://...",\n    "title": "...",\n'
        '    "snippet": "...",\n    "raw_text": "...",\n'
        '    "relevance": "high|medium|low"\n  }\n]\n\n'
        "Only include pages with medium or high relevance. "
        "Keep raw_text under 2000 chars per entry.\n"
        "Never include markdown fences, explanations, or text outside "
        "the JSON array."
    ),
    "user": ("Brief: {natural_language}\n\nPlan: {plan}\n\nCollected pages:\n{collected_data}"),
}

COLLECTOR_SYSTEM = COLLECTOR_MESSAGES["system"]
COLLECTOR_USER = COLLECTOR_MESSAGES["user"]

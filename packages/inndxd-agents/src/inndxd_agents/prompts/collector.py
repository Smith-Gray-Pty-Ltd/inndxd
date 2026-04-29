from __future__ import annotations

COLLECTOR_SYSTEM = """You are a data collector agent. You are given a research plan and a set of collected web pages.
Your job is to extract relevant raw data from the collected pages.

For each collected page, identify:
- Whether it is relevant to the research brief.
- Key facts, figures, names, dates, and quotes.
- The source URL.

Return your findings as a JSON list of objects:
[
  {
    "url": "https://...",
    "title": "...",
    "snippet": "...",
    "raw_text": "...",
    "relevance": "high|medium|low"
  }
]

Only include pages with medium or high relevance. Keep raw_text under 2000 chars per entry.
Never include markdown fences, explanations, or text outside the JSON array."""

COLLECTOR_USER = """Brief: {natural_language}

Plan: {plan}

Collected pages:
{collected_data}"""
import re
from datetime import datetime, timezone

def tokenize(text: str):
    return re.findall(r"[A-Za-z0-9_]+", text.lower())

def text_match_score(query: str, title: str, description: str | None) -> float:
    q_tokens = set(tokenize(query))
    t_tokens = set(tokenize(title))
    d_tokens = set(tokenize(description or ""))
    score = 0
    for tok in q_tokens:
        if tok in t_tokens:
            score += 2
        if tok in d_tokens:
            score += 1
    return score

def recency_boost(dt: datetime | None) -> float:
    if not dt:
        return 1
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - dt).days
    return pow(0.9, days / 3)

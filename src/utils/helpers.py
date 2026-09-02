"""Helper and utility functions."""

import json
import re
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def clean_json_string(text: str) -> str:
    """Extract a clean JSON string from LLM responses that might contain markdown blocks."""
    if not text:
        return "{}"

    # Trim whitespace
    text = text.strip()

    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()

    # If starts with { or [, try to find matching closing bracket
    first_brace = text.find("{")
    first_bracket = text.find("[")

    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        last_brace = text.rfind("}")
        if last_brace != -1:
            return text[first_brace : last_brace + 1].strip()

    if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
        last_bracket = text.rfind("]")
        if last_bracket != -1:
            return text[first_bracket : last_bracket + 1].strip()

    return text


def parse_json_safely(text: str, default: Any = None) -> Any:
    """Safely parse JSON text, falling back to default if parsing fails."""
    try:
        clean_text = clean_json_string(text)
        return json.loads(clean_text)
    except Exception:
        return default if default is not None else {}


def extract_domain(url: Optional[str]) -> str:
    """Extract domain from URL, e.g. 'https://www.vision2030.gov.sa/path' -> 'vision2030.gov.sa'."""
    if not url:
        return "web_grounding"
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        # Remove port if present
        domain = domain.split(":")[0]
        # Remove 'www.' prefix for clean presentation
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or "web_grounding"
    except Exception:
        return "web_grounding"


def classify_source_type(url: Optional[str], title: Optional[str]) -> str:
    """Classify the source type based on domain and title heuristics."""
    domain = extract_domain(url).lower()
    title_lower = (title or "").lower()

    if any(gov in domain for gov in [".gov", ".mil", "ministry", "sdaia", "stats.gov"]):
        return "official_government"
    if any(edu in domain for edu in [".edu", ".ac.", "arxiv", "researchgate", "scholar", "nature.com", "ieee"]):
        return "academic_research"
    if any(news in domain for news in ["reuters", "bloomberg", "wsj", "ft.com", "cnbc", "arabnews", "techcrunch", "forbes", "bbc"]):
        return "reputable_news"
    if any(ind in domain for ind in ["gartner", "mckinsey", "pwc", "deloitte", "kpmg", "idc.com", "statista"]):
        return "industry_report"
    return "general_web"


def generate_id(prefix: str = "item") -> str:
    """Generate a short unique ID with a specified prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length with ellipsis if needed."""
    if not text or len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."

"""Unit tests for search tools and utility functions."""

import pytest
from src.tools.tools import get_current_datetime, perform_calculation
from src.tools.web_search import WebSearchTool
from src.utils.helpers import classify_source_type, clean_json_string, extract_domain, parse_json_safely


def test_domain_extraction():
    assert extract_domain("https://www.reuters.com/world/middle-east") == "reuters.com"
    assert extract_domain("https://sdaia.gov.sa/en/default.aspx") == "sdaia.gov.sa"
    assert extract_domain("https://sub.domain.co.uk:8080/path") == "sub.domain.co.uk"
    assert extract_domain(None) == "web_grounding"


def test_source_classification():
    assert classify_source_type("https://www.stats.gov.sa", "National Statistics") == "official_government"
    assert classify_source_type("https://arxiv.org/abs/2301.0000", "AI Paper") == "academic_research"
    assert classify_source_type("https://www.bloomberg.com/news", "Market Report") == "reputable_news"
    assert classify_source_type("https://www.mckinsey.com/capabilities", "Strategy Report") == "industry_report"
    assert classify_source_type("https://myrandomblog.com/post", "Blog") == "general_web"


def test_json_cleaner_and_parser():
    raw_md = '```json\n{"key": "value", "numbers": [1, 2, 3]}\n```'
    clean = clean_json_string(raw_md)
    assert clean == '{"key": "value", "numbers": [1, 2, 3]}'

    parsed = parse_json_safely(raw_md)
    assert parsed["key"] == "value"
    assert parsed["numbers"] == [1, 2, 3]

    invalid_json = "This is not json"
    assert parse_json_safely(invalid_json, default={"fallback": True}) == {"fallback": True}


def test_calculation_tool():
    assert perform_calculation(10, 5, "add") == 15
    assert perform_calculation(10, 5, "subtract") == 5
    assert perform_calculation(10, 5, "multiply") == 50
    assert perform_calculation(10, 5, "divide") == 2.0
    assert "Cannot" in str(perform_calculation(10, 0, "divide")) or "Division by zero" in str(perform_calculation(10, 0, "divide"))


def test_datetime_tool():
    dt_str = get_current_datetime()
    assert len(dt_str) == 19  # YYYY-MM-DD HH:MM:SS format


def test_web_search_mock_mode():
    tool = WebSearchTool(mock_mode=True)
    sources, evidence, summary = tool.search(query="Saudi Arabia AI Market")

    assert len(sources) >= 2
    assert len(evidence) >= 2
    assert "Saudi" in sources[0].title or "Insights" in sources[0].title
    assert sources[0].reliability_score >= 0.85
    assert len(summary) > 20

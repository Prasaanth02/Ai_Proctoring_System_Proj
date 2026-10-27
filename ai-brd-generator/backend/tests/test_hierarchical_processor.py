import pytest
from unittest.mock import patch, MagicMock
from backend.app.hierarchical_processor import (
    extract_from_chunk,
    aggregate,
    format_for_final_generation,
    empty_intermediate,
    BRD_KEYS,
)
from backend.app.brd_generator import generate_final_brd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chunk(chunk_id: int, text: str) -> dict:
    return {"chunk_id": chunk_id, "text": text, "source": "test.pdf", "token_count": 50}


def _mock_llm(content: str):
    msg = MagicMock(); msg.content = content
    choice = MagicMock(); choice.message = msg
    resp = MagicMock(); resp.choices = [choice]
    return resp


_SAMPLE_JSON = """{
  "business_problem": ["The company lacks an automated leave management system."],
  "objectives": ["Automate leave request processing."],
  "stakeholders": ["HR Manager", "Employees"],
  "functional_requirements": ["Employees can submit leave requests online."],
  "non_functional_requirements": ["System must respond within 2 seconds."],
  "business_rules": ["Leave requests require manager approval."],
  "assumptions": ["All employees have internet access."],
  "constraints": ["Must integrate with existing HR system."],
  "dependencies": ["HR database must be available."],
  "risks": ["Low user adoption if UI is complex."],
  "success_criteria": ["90% of leave requests processed within 1 day."]
}"""


# ---------------------------------------------------------------------------
# Single chunk extraction
# ---------------------------------------------------------------------------

@patch("backend.app.hierarchical_processor.OpenAI")
def test_extract_from_single_chunk(mock_cls):
    mock_cls.return_value.chat.completions.create.return_value = _mock_llm(_SAMPLE_JSON)
    chunk = _make_chunk(1, "Employees should be able to apply for leave online.")
    result = extract_from_chunk(chunk)

    assert len(result["functional_requirements"]) == 1
    assert result["functional_requirements"][0]["text"] == "Employees can submit leave requests online."
    assert result["functional_requirements"][0]["source_chunk"] == 1


@patch("backend.app.hierarchical_processor.OpenAI")
def test_extract_attaches_source_chunk(mock_cls):
    mock_cls.return_value.chat.completions.create.return_value = _mock_llm(_SAMPLE_JSON)
    result = extract_from_chunk(_make_chunk(3, "Some requirement text."))
    for key in BRD_KEYS:
        for item in result[key]:
            assert item["source_chunk"] == 3


# ---------------------------------------------------------------------------
# Empty / failed chunk handling
# ---------------------------------------------------------------------------

def test_extract_empty_chunk_returns_empty():
    result = extract_from_chunk(_make_chunk(1, ""))
    assert result == empty_intermediate()


@patch("backend.app.hierarchical_processor.OpenAI")
def test_extract_failed_llm_returns_empty(mock_cls):
    mock_cls.return_value.chat.completions.create.side_effect = Exception("API error")
    result = extract_from_chunk(_make_chunk(1, "Some text."))
    assert result == empty_intermediate()


@patch("backend.app.hierarchical_processor.OpenAI")
def test_extract_malformed_json_returns_empty(mock_cls):
    mock_cls.return_value.chat.completions.create.return_value = _mock_llm("not valid json at all")
    result = extract_from_chunk(_make_chunk(1, "Some text."))
    assert result == empty_intermediate()


# ---------------------------------------------------------------------------
# Multiple chunk processing
# ---------------------------------------------------------------------------

@patch("backend.app.hierarchical_processor.OpenAI")
def test_extract_multiple_chunks(mock_cls):
    mock_cls.return_value.chat.completions.create.return_value = _mock_llm(_SAMPLE_JSON)
    chunks = [_make_chunk(i, f"Requirement text {i}.") for i in range(1, 4)]
    results = [extract_from_chunk(c) for c in chunks]
    assert len(results) == 3
    for r in results:
        assert "functional_requirements" in r


# ---------------------------------------------------------------------------
# Intermediate structure validation
# ---------------------------------------------------------------------------

@patch("backend.app.hierarchical_processor.OpenAI")
def test_intermediate_has_all_keys(mock_cls):
    mock_cls.return_value.chat.completions.create.return_value = _mock_llm(_SAMPLE_JSON)
    result = extract_from_chunk(_make_chunk(1, "Some text."))
    for key in BRD_KEYS:
        assert key in result


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

@patch("backend.app.hierarchical_processor.OpenAI")
def test_aggregation_merges_chunks(mock_cls):
    json1 = '{"business_problem":["Problem A"],"objectives":[],"stakeholders":[],' \
            '"functional_requirements":["FR A"],"non_functional_requirements":[],' \
            '"business_rules":[],"assumptions":[],"constraints":[],' \
            '"dependencies":[],"risks":[],"success_criteria":[]}'
    json2 = '{"business_problem":["Problem B"],"objectives":[],"stakeholders":[],' \
            '"functional_requirements":["FR B"],"non_functional_requirements":[],' \
            '"business_rules":[],"assumptions":[],"constraints":[],' \
            '"dependencies":[],"risks":[],"success_criteria":[]}'

    mock_cls.return_value.chat.completions.create.side_effect = [
        _mock_llm(json1), _mock_llm(json2)
    ]
    r1 = extract_from_chunk(_make_chunk(1, "Chunk 1 text."))
    r2 = extract_from_chunk(_make_chunk(2, "Chunk 2 text."))
    combined = aggregate([r1, r2])

    assert len(combined["business_problem"]) == 2
    assert len(combined["functional_requirements"]) == 2


def test_aggregation_deduplicates():
    r1 = empty_intermediate()
    r2 = empty_intermediate()
    r1["functional_requirements"].append({"text": "Same requirement.", "source_chunk": 1})
    r2["functional_requirements"].append({"text": "Same requirement.", "source_chunk": 2})
    combined = aggregate([r1, r2])
    assert len(combined["functional_requirements"]) == 1


def test_aggregation_dedup_case_insensitive():
    r1 = empty_intermediate()
    r2 = empty_intermediate()
    r1["functional_requirements"].append({"text": "Same requirement.", "source_chunk": 1})
    r2["functional_requirements"].append({"text": "same requirement.", "source_chunk": 2})
    combined = aggregate([r1, r2])
    assert len(combined["functional_requirements"]) == 1


# ---------------------------------------------------------------------------
# Requirement ID generation
# ---------------------------------------------------------------------------

def test_requirement_ids_assigned():
    r = empty_intermediate()
    r["functional_requirements"] = [
        {"text": "FR one.", "source_chunk": 1},
        {"text": "FR two.", "source_chunk": 1},
    ]
    r["non_functional_requirements"] = [
        {"text": "NFR one.", "source_chunk": 1},
    ]
    combined = aggregate([r])
    assert combined["functional_requirements"][0]["id"] == "FR-001"
    assert combined["functional_requirements"][1]["id"] == "FR-002"
    assert combined["non_functional_requirements"][0]["id"] == "NFR-001"


def test_no_duplicate_requirement_ids():
    r = empty_intermediate()
    r["functional_requirements"] = [
        {"text": f"Requirement {i}.", "source_chunk": 1} for i in range(5)
    ]
    combined = aggregate([r])
    ids = [item["id"] for item in combined["functional_requirements"]]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Source chunk tracking
# ---------------------------------------------------------------------------

@patch("backend.app.hierarchical_processor.OpenAI")
def test_source_chunk_preserved_through_aggregation(mock_cls):
    mock_cls.return_value.chat.completions.create.return_value = _mock_llm(_SAMPLE_JSON)
    r = extract_from_chunk(_make_chunk(7, "Some text."))
    combined = aggregate([r])
    for key in BRD_KEYS:
        for item in combined[key]:
            assert item["source_chunk"] == 7


# ---------------------------------------------------------------------------
# Preservation of requirements
# ---------------------------------------------------------------------------

def test_aggregation_preserves_all_unique_requirements():
    r1 = empty_intermediate()
    r1["functional_requirements"] = [{"text": f"Req {i}.", "source_chunk": 1} for i in range(5)]
    combined = aggregate([r1])
    assert len(combined["functional_requirements"]) == 5


# ---------------------------------------------------------------------------
# format_for_final_generation
# ---------------------------------------------------------------------------

def test_format_includes_requirement_ids():
    r = empty_intermediate()
    r["functional_requirements"] = [{"text": "User login.", "source_chunk": 1, "id": "FR-001"}]
    text = format_for_final_generation(aggregate([r]))
    assert "FR-001" in text


def test_format_marks_empty_sections():
    combined = empty_intermediate()
    text = format_for_final_generation(combined)
    assert "Not specified in the provided requirements." in text


# ---------------------------------------------------------------------------
# Final BRD generation (mocked)
# ---------------------------------------------------------------------------

@patch("backend.app.brd_generator.OpenAI")
def test_generate_final_brd_returns_markdown(mock_cls):
    mock_cls.return_value.chat.completions.create.return_value = _mock_llm(
        "# Business Requirements Document\n\n## 1. Project Title\nTest"
    )
    result = generate_final_brd("### Functional Requirements\nFR-001: User login.")
    assert "# Business Requirements Document" in result


@patch("backend.app.brd_generator.OpenAI")
def test_generate_final_brd_empty_raises(mock_cls):
    from backend.app.brd_generator import generate_final_brd
    with pytest.raises(ValueError, match="empty"):
        generate_final_brd("")

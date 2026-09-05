"""Tests for /api/competency endpoints."""

from unittest.mock import patch


def test_get_framework(client):
    resp = client.get("/api/competency/framework")
    assert resp.status_code == 200
    body = resp.json()
    assert "statistical" in body
    assert "technical" in body
    assert isinstance(body["statistical"]["skills"], list)


@patch("app.api.competency.skill_analyzer")
def test_assess_competencies(mock_analyzer, client, auth_headers):
    mock_analyzer.generate_competency_report.return_value = {
        "user_id": 1,
        "competency_levels": {"Python": 3.0, "SQL": 2.5},
        "skill_gaps": [{"skill": "Python", "current_level": 3.0, "target_level": 4.0, "gap": 1.0, "priority": "medium"}],
        "category_summary": {"technical": {"average_level": 2.75, "skills_assessed": 2, "total_skills": 14}},
        "overall_score": 2.75,
        "recommendations": ["Focus on Python"],
    }
    resp = client.post("/api/competency/assess",
        json={"skills": ["Python", "SQL"], "experience": 3}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "Python" in body["competency_levels"]
    assert body["overall_score"] > 0


@patch("app.api.competency.skill_analyzer")
def test_get_gaps(mock_analyzer, client, auth_headers):
    mock_analyzer.identify_gaps.return_value = [
        {"skill": "Python", "current_level": 2.0, "target_level": 3.0, "gap": 1.0, "priority": "medium"}
    ]
    resp = client.get("/api/competency/gaps", headers=auth_headers)
    assert resp.status_code == 200
    assert "skill_gaps" in resp.json()


@patch("app.api.competency.skill_analyzer")
def test_get_report(mock_analyzer, client, auth_headers):
    mock_analyzer.identify_gaps.return_value = []
    resp = client.get("/api/competency/report", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "competency_levels" in body
    assert "overall_score" in body

"""Tests for /api/recommendation endpoints."""

from unittest.mock import patch


@patch("app.api.recommendation.rec_engine")
def test_learning_path(mock_engine, client, auth_headers):
    mock_engine.generate_learning_path.return_value = {
        "skill_gaps": [{"skill": "Python", "current_level": 0, "target_level": 3.0, "gap": 3.0, "priority": "high"}],
        "recommended_courses": [{"id": "IGOT001", "title": "Python Course", "relevance_score": 0.9}],
        "total_courses": 1,
        "estimated_duration_hours": 2,
        "estimated_completion_days": 7,
        "learning_milestones": [{"milestone": 1, "course": "Python Course"}],
    }
    resp = client.post("/api/recommendation/learning-path", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "skill_gaps" in body
    assert "recommended_courses" in body


def test_active_path_none(client, auth_headers):
    resp = client.get("/api/recommendation/active-path", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    # Either no active path or there is one — both are valid
    assert "message" in body or "path" in body or "id" in body

"""Tests for /api/quiz endpoints."""

from unittest.mock import patch


@patch("app.api.quiz.mcq_generator")
def test_generate_quiz(mock_gen, client, auth_headers):
    mock_gen.generate_mcqs_from_text.return_value = [
        {"id": 1, "question": "What is Python?", "options": ["Language", "Snake", "Tool", "OS"],
         "correct_answer": "A", "explanation": "Python is a programming language", "difficulty": "medium", "concept": "Python"}
    ]
    resp = client.post("/api/quiz/generate",
        json={"text": "Python is a programming language", "num_questions": 1}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_questions"] == 1
    assert "id" in body


@patch("app.api.quiz.mcq_generator")
def test_generate_quiz_concept(mock_gen, client, auth_headers):
    mock_gen.generate_mcqs_from_concept.return_value = [
        {"id": 1, "question": "What is ML?", "options": ["AI", "DB", "OS", "Net"],
         "correct_answer": "A", "explanation": "ML is AI", "difficulty": "medium", "concept": "ML"}
    ]
    resp = client.post("/api/quiz/generate",
        json={"concept": "Machine Learning", "num_questions": 1}, headers=auth_headers)
    assert resp.status_code == 200


def test_generate_quiz_no_input(client, auth_headers):
    resp = client.post("/api/quiz/generate", json={"num_questions": 1}, headers=auth_headers)
    assert resp.status_code == 400


def test_quiz_history(client, auth_headers):
    resp = client.get("/api/quiz/history", headers=auth_headers)
    assert resp.status_code == 200
    assert "attempts" in resp.json()


def test_get_quiz_not_found(client, auth_headers):
    resp = client.get("/api/quiz/99999", headers=auth_headers)
    assert resp.status_code == 404

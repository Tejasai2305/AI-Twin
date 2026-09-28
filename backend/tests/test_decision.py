def test_decision_compare_requires_two_options(client):
    r = client.post("/decision/compare", json={"options": ["only one"], "criteria": ["speed"]})
    assert r.status_code == 422


def test_decision_compare_requires_at_least_one_criterion(client):
    r = client.post("/decision/compare", json={"options": ["A", "B"], "criteria": []})
    assert r.status_code == 422


def test_decision_compare_returns_structured_result(client, mock_gemini):
    mock_gemini(lambda prompt: '''
    {
      "options": [
        {"name": "A", "scores": {"speed": {"score": 8, "justification": "fast"}}, "weighted_total": 8},
        {"name": "B", "scores": {"speed": {"score": 4, "justification": "slow"}}, "weighted_total": 4}
      ],
      "assumptions": ["assumed speed means runtime"],
      "trade_offs": ["A is faster but B is simpler"],
      "recommendation": "Go with A if speed matters most."
    }
    ''')

    r = client.post("/decision/compare", json={"options": ["A", "B"], "criteria": ["speed"]})
    assert r.status_code == 200
    body = r.json()
    assert len(body["options"]) == 2
    assert body["recommendation"]


def test_decision_compare_handles_malformed_model_output_gracefully(client, mock_gemini):
    mock_gemini(lambda prompt: "Sorry, I can't help with that in JSON form.")

    r = client.post("/decision/compare", json={"options": ["A", "B"], "criteria": ["speed"]})
    assert r.status_code == 200
    assert "error" in r.json()


def test_decision_compare_strips_markdown_fences(client, mock_gemini):
    mock_gemini(lambda prompt: '''```json
    {"options": [{"name": "A", "scores": {}, "weighted_total": 1}, {"name": "B", "scores": {}, "weighted_total": 2}],
     "assumptions": [], "trade_offs": [], "recommendation": "B wins"}
    ```''')

    r = client.post("/decision/compare", json={"options": ["A", "B"], "criteria": ["x"]})
    assert r.status_code == 200
    assert r.json()["recommendation"] == "B wins"

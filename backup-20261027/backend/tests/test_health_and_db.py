def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["demo_profiles_count"] == 3

def test_demo_users_endpoint(client):
    response = client.get("/api/users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 3
    user_ids = {u["id"] for u in users}
    assert user_ids == {"demo-user-1", "demo-user-2", "demo-user-3"}
    for u in users:
        assert u["label"] == "SYNTHETIC / DEMO PROFILE"
        assert len(u["preferred_genres"]) > 0

def test_user_preferences_endpoint(client):
    response = client.get("/api/users/demo-user-1/preferences")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "demo-user-1"
    assert "indie rock" in data["preferred_genres"]
    assert "stats" in data

def test_diagnostics_providers_status(client):
    response = client.get("/api/diagnostics/providers")
    assert response.status_code == 200
    providers = response.json()
    assert len(providers) >= 4
    names = [p["provider"] for p in providers]
    assert any("MusicBrainz" in n for n in names)
    assert any("Last.fm" in n for n in names)
    assert any("YouTube" in n for n in names)
    assert any("Pitchfork" in n for n in names)

def test_diagnostics_logs_redaction(client):
    response = client.get("/api/diagnostics/logs")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    # Ensure no secrets leak
    for l in logs:
        text_str = str(l).lower()
        assert "secret_key" not in text_str
        assert "password" not in text_str

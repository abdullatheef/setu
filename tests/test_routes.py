def test_signup(client):
    """Test user signup"""
    response = client.post("/auth/signup", json={"username": "test", "password": "pass"})
    assert response.status_code == 201  # Adjust based on your API response

def test_login(client):
    """Test login functionality after signing up"""
    # Ensure the user exists
    client.post("/auth/signup", json={"username": "test", "password": "pass"})

    # Try logging in
    response = client.post("/auth/login", json={"username": "test", "password": "pass"})
    assert response.status_code == 200
    assert "token" in response.json  # Modify if your auth response is different


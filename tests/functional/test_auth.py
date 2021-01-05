"""Test /auth endpoint."""


def test_auth(test_client, new_user):
    """Check for status code and for access_token in the response object."""
    response = test_client.post(
        "/auth", json={"username": "mole", "password": "desert"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json

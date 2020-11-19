"""Test squash-api models."""


def test_new_user(new_user):
    """Test user cretion with hashed password."""
    assert new_user.username == "mole"
    assert new_user.verify_password("desert") is True

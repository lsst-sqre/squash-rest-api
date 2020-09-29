"""Implement helper functions for authentication."""

__all__ = ["authenticate", "identity"]

from .models import UserModel


def authenticate(username, password):
    """Verify user password."""
    user = UserModel.find_by_username(username)
    if user and user.verify_password(password):
        return user


def identity(payload):
    """Find user from its id."""
    user_id = payload["identity"]
    return UserModel.find_by_id(user_id)

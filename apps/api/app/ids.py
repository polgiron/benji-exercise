import secrets


def new_id(prefix: str) -> str:
    """Prefixed random id, e.g. `ep_3fZk9…`, readable in logs and the UI."""
    return f"{prefix}_{secrets.token_urlsafe(12)}"

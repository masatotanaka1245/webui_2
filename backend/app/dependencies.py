from .schemas import DevelopmentUser


def get_current_development_user() -> DevelopmentUser:
    """Development-only identity provider; replace with authenticated identity later."""
    return DevelopmentUser(user_id="dev-user", role="system_admin")

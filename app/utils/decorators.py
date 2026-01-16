"""
Custom Decorators
"""
from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    """
    Decorator to require admin access for a view
    Must be used after @login_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

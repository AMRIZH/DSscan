"""
Views Package
"""
from .main import main_bp
from .auth import auth_bp
from .dashboard import dashboard_bp
from .records import records_bp

__all__ = ['main_bp', 'auth_bp', 'dashboard_bp', 'records_bp']

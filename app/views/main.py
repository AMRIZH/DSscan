"""
Main Views (Homepage)
"""
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage"""
    return render_template('index.html')


@main_bp.route('/tentang')
def about():
    """About page"""
    return render_template('about.html')

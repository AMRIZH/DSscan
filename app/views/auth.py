"""
Authentication Views
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length

from ..models.user import User
from ..extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username wajib diisi'),
        Length(min=3, max=80, message='Username harus 3-80 karakter')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password wajib diisi')
    ])
    remember_me = BooleanField('Ingat saya')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Login user with remember option (30 days)
            login_user(user, remember=form.remember_me.data)
            
            current_app.logger.info(f"User '{username}' logged in successfully")
            flash(f'Selamat datang, {user.username}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            current_app.logger.warning(f"Failed login attempt for username: '{username}'")
            flash('Username atau password salah.', 'danger')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    username = current_user.username
    logout_user()
    current_app.logger.info(f"User '{username}' logged out")
    flash('Anda telah berhasil keluar.', 'info')
    return redirect(url_for('main.index'))

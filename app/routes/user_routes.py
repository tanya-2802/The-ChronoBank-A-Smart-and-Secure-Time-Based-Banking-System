from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db
from werkzeug.security import generate_password_hash
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Render the home page."""
    if current_user.is_authenticated:
        return redirect(url_for('account.dashboard'))
    return render_template('login.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('account.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('account.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('account.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Render the user profile page."""
    return render_template('profile.html')

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Handle user profile editing."""
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        
        # Check if email already exists
        if email != current_user.email:
            existing_user = User.query.filter_by(email=email).first()
            
            if existing_user:
                flash('Email already exists', 'danger')
                return render_template('edit_profile.html')
        
        # Update user
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('edit_profile.html')

@auth_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Handle user password change."""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if current password is correct
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return render_template('change_password.html')
        
        # Check if new password and confirmation match
        if new_password != confirm_password:
            flash('New password and confirmation do not match', 'danger')
            return render_template('change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('change_password.html')

"""
Authentication routes for user login and management.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from models.user import User
from models.tenant import Tenant
from utils.tenant import get_current_tenant, get_tenant_id
from utils.decorators import tenant_required
from app import db, mail
import re

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    """Check if password meets strength requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

@auth_bp.route('/register', methods=['POST'])
@tenant_required
def register():
    """User registration endpoint."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request data required'}), 400
    
    # Validate required fields
    required_fields = ['email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field.title()} is required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    
    # Validate email format
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password strength
    is_strong, message = is_strong_password(password)
    if not is_strong:
        return jsonify({'error': message}), 400
    
    # Get current tenant
    tenant = get_current_tenant()
    
    # Check if user already exists in this tenant
    existing_user = User.query.filter_by(
        email=email,
        tenant_id=tenant.id
    ).first()
    
    if existing_user:
        return jsonify({'error': 'User with this email already exists'}), 409
    
    # Create new user
    user = User(
        email=email,
        first_name=data.get('first_name', '').strip(),
        last_name=data.get('last_name', '').strip(),
        language=data.get('language', 'en'),
        tenant_id=tenant.id
    )
    user.set_password(password)
    
    # Set first user as admin
    user_count = User.query.filter_by(tenant_id=tenant.id).count()
    if user_count == 0:
        user.role = 'admin'
        user.is_verified = True  # First user is auto-verified
    else:
        # Generate verification token for email verification
        user.generate_verification_token()
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Send verification email if not first user
        if user.role != 'admin':
            send_verification_email(user, tenant)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'requires_verification': not user.is_verified
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to register user'}), 500

@auth_bp.route('/login', methods=['POST'])
@tenant_required
def login():
    """User login endpoint."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    
    # Get current tenant
    tenant = get_current_tenant()
    
    # Find user by email within tenant
    user = User.query.filter_by(
        email=email,
        tenant_id=tenant.id
    ).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Update login information
    user.update_login_info()
    db.session.commit()
    
    # Log user in
    login_user(user, remember=data.get('remember', False))
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'tenant': tenant.to_dict()
    })

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout endpoint."""
    logout_user()
    return jsonify({'message': 'Logout successful'})

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current authenticated user."""
    return jsonify({
        'user': current_user.to_dict(include_sensitive=True)
    })

@auth_bp.route('/verify-email/<token>', methods=['POST'])
def verify_email(token):
    """Verify user email with token."""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        return jsonify({'error': 'Invalid verification token'}), 400
    
    if user.verify_email_token(token):
        db.session.commit()
        return jsonify({'message': 'Email verified successfully'})
    else:
        return jsonify({'error': 'Verification token expired'}), 400

@auth_bp.route('/forgot-password', methods=['POST'])
@tenant_required
def forgot_password():
    """Request password reset."""
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    email = data['email'].lower().strip()
    tenant = get_current_tenant()
    
    user = User.query.filter_by(
        email=email,
        tenant_id=tenant.id
    ).first()
    
    if user:
        token = user.generate_reset_token()
        db.session.commit()
        send_password_reset_email(user, tenant, token)
    
    # Always return success to prevent email enumeration
    return jsonify({'message': 'If the email exists, a reset link has been sent'})

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token."""
    data = request.get_json()
    
    if not data or not data.get('token') or not data.get('password'):
        return jsonify({'error': 'Token and new password required'}), 400
    
    token = data['token']
    password = data['password']
    
    # Validate password strength
    is_strong, message = is_strong_password(password)
    if not is_strong:
        return jsonify({'error': message}), 400
    
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    user.set_password(password)
    user.clear_reset_token()
    db.session.commit()
    
    return jsonify({'message': 'Password reset successfully'})

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    data = request.get_json()
    
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current and new password required'}), 400
    
    current_password = data['current_password']
    new_password = data['new_password']
    
    if not current_user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    # Validate new password strength
    is_strong, message = is_strong_password(new_password)
    if not is_strong:
        return jsonify({'error': message}), 400
    
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'})

@auth_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    """Get or update user profile."""
    if request.method == 'GET':
        return jsonify({'user': current_user.to_dict(include_sensitive=True)})
    
    # PUT - Update profile
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request data required'}), 400
    
    # Update allowed fields
    if 'first_name' in data:
        current_user.first_name = data['first_name'].strip()
    if 'last_name' in data:
        current_user.last_name = data['last_name'].strip()
    if 'language' in data and data['language'] in ['en', 'fr']:
        current_user.language = data['language']
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500

def send_verification_email(user, tenant):
    """Send email verification email."""
    try:
        msg = Message(
            subject=f'Verify your email for {tenant.name}',
            recipients=[user.email],
            html=f'''
            <h2>Welcome to {tenant.name}!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{tenant.get_url()}/verify-email/{user.verification_token}">Verify Email</a></p>
            <p>This link will expire in 7 days.</p>
            '''
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {e}")

def send_password_reset_email(user, tenant, token):
    """Send password reset email."""
    try:
        msg = Message(
            subject=f'Password Reset for {tenant.name}',
            recipients=[user.email],
            html=f'''
            <h2>Password Reset Request</h2>
            <p>You requested a password reset for your account at {tenant.name}.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{tenant.get_url()}/reset-password/{token}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this reset, please ignore this email.</p>
            '''
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {e}")

{{ ... }}
from flask import Blueprint, request, jsonify, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from models.user import User
from models.tenant import Tenant
from utils.tenant import get_current_tenant, get_tenant_id
from utils.decorators import tenant_required
from app import db, mail, limiter, csrf
import re
{{ ... }}
@auth_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    """Return a CSRF token for SPA clients. Include it as X-CSRFToken header in future unsafe requests."""
    token = generate_csrf()
    return jsonify({'csrfToken': token})

@auth_bp.route('/login', methods=['POST'])
@tenant_required
@limiter.limit("5 per minute")
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
    
    # Bind session to tenant context
    session['tenant_id'] = tenant.id
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'tenant': tenant.to_dict()
    })
{{ ... }}
@auth_bp.route('/verify-email/<token>', methods=['POST'])
@limiter.limit("20 per hour")
@csrf.exempt
def verify_email(token):
    """Verify user email with token."""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        return jsonify({'error': 'Invalid verification token'}), 400
{{ ... }}
@auth_bp.route('/forgot-password', methods=['POST'])
@tenant_required
@limiter.limit("5 per hour")
def forgot_password():
    """Request password reset."""
    data = request.get_json()
{{ ... }}
@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per hour")
def reset_password():
    """Reset password with token."""
    data = request.get_json()
{{ ... }}

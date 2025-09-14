"""
Authentication and tenant management routes.
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models.user import User
from models.tenant import Tenant
from utils.tenant import get_current_tenant

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Get current tenant context
    tenant = get_current_tenant()
    if not tenant:
        return jsonify({'error': 'Invalid tenant'}), 400
    
    # Find user within tenant
    user = User.query.filter_by(email=email, tenant_id=tenant.id).first()
    
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'is_admin': user.is_admin
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout endpoint."""
    logout_user()
    return jsonify({'message': 'Logout successful'})

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information."""
    return jsonify({
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'is_admin': current_user.is_admin,
            'tenant_id': current_user.tenant_id
        }
    })

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from app import db, mail
from models.user import User
from models.tenant import Tenant
from models.admin_invitation import AdminInvitation
from utils.decorators import tenant_admin_required, tenant_required
from utils.tenant import get_current_tenant
import re

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/init-db', methods=['POST'])
def init_database():
    """Initialize database tables - REMOVE THIS IN PRODUCTION!"""
    try:
        db.create_all()
        return jsonify({'message': 'Database tables created successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

ALLOWED_ROLES = {'user', 'admin', 'super_admin'}
ASSIGNABLE_ROLES_BY_ROLE = {
    'admin': {'user', 'admin'},  # tenant admin cannot grant super_admin
    'super_admin': {'user', 'admin', 'super_admin'}
}

# ============ Admin Invitations ============

@admin_bp.route('/invitations', methods=['POST'])
@tenant_admin_required
def invite_admin():
    """
    Endpoint for an admin to invite a new user (e.g., team manager) to their tenant.
    The role of the invited user is specified in the request.
    """
    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'admin') # Default to 'admin' if not specified

    # Validate role
    assignable_roles = ASSIGNABLE_ROLES_BY_ROLE.get(current_user.role, set())
    if role not in assignable_roles:
        return jsonify({'error': f'You do not have permission to assign the role: {role}.'}), 403

    if not email or not is_valid_email(email):
        return jsonify({'error': 'A valid email is required.'}), 400

    tenant = get_current_tenant()
    existing_user = User.query.filter_by(email=email, tenant_id=tenant.id).first()
    if existing_user:
        return jsonify({'error': 'A user with this email already exists in your organization.'}), 409

    existing_invitation = AdminInvitation.query.filter_by(email=email, tenant_id=tenant.id, status='pending').first()
    if existing_invitation and existing_invitation.is_valid():
        return jsonify({'error': 'An active invitation for this email already exists.'}), 409

    invitation = AdminInvitation(
        email=email,
        tenant_id=tenant.id,
        invited_by_id=current_user.id,
        role=role
    )
    db.session.add(invitation)
    db.session.commit()

    try:
        _send_admin_invitation_email(invitation, tenant)
    except Exception as e:
        current_app.logger.error(f"Failed to send admin invitation email to {email}: {e}")

    return jsonify({
        'message': f'Invitation for role `{role}` sent successfully to {email}.',
        'invitation': invitation.to_dict()
    }), 201

def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email or '') is not None

# ============ Users management ============
@admin_bp.route('/users', methods=['GET'])
@tenant_admin_required
def list_users():
    tenant = get_current_tenant()
    q = User.query.filter_by(tenant_id=tenant.id)
    # Filters
    role = request.args.get('role')
    if role in ALLOWED_ROLES:
        q = q.filter(User.role == role)
    active = request.args.get('active')
    if active in ['true','false','1','0']:
        q = q.filter(User.is_active == (active in ['true','1']))
    search = request.args.get('search', '').strip()
    if search:
        like = f"%{search.lower()}%"
        q = q.filter(db.or_(db.func.lower(User.email).like(like)))
    users = q.order_by(User.created_at.desc()).all()
    return jsonify({'users': [u.to_dict() for u in users], 'total': len(users)})

@admin_bp.route('/users/invite', methods=['POST'])
@tenant_admin_required
def invite_user():
    tenant = get_current_tenant()
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    first_name = (data.get('first_name') or '').strip() or 'User'
    last_name = (data.get('last_name') or '').strip() or 'Name'
    role = (data.get('role') or 'user').strip()

    # Validate
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email'}), 400
    if role not in ASSIGNABLE_ROLES_BY_ROLE.get(current_user.role, {'user'}):
        return jsonify({'error': 'Insufficient privileges to assign this role'}), 403
    if User.query.filter_by(email=email, tenant_id=tenant.id).first():
        return jsonify({'error': 'User with this email already exists'}), 409

    # Create user (unverified)
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=role,
        tenant_id=tenant.id,
        is_active=True,
        is_verified=False
    )
    # Generate verification token
    user.generate_verification_token()

    try:
        db.session.add(user)
        db.session.commit()
        _send_verification_email(user, tenant)
        return jsonify({
            'message': 'Invitation sent successfully',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to invite user: {e}")
        return jsonify({'error': 'Failed to invite user'}), 500

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@tenant_admin_required
def update_user_role(user_id: int):
    tenant = get_current_tenant()
    user = User.query.filter_by(id=user_id, tenant_id=tenant.id).first_or_404()

    data = request.get_json() or {}
    new_role = (data.get('role') or '').strip()
    if new_role not in ASSIGNABLE_ROLES_BY_ROLE.get(current_user.role, set()):
        return jsonify({'error': 'Insufficient privileges to assign this role'}), 403

    # Prevent demoting the last admin
    if user.role in {'admin', 'super_admin'} and new_role == 'user':
        admin_count = User.query.filter_by(tenant_id=tenant.id).filter(User.role.in_(['admin','super_admin'])).count()
        if admin_count <= 1:
            return jsonify({'error': 'Cannot demote the last admin of this tenant'}), 400

    user.role = new_role
    try:
        db.session.commit()
        return jsonify({'message': 'Role updated', 'user': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update role: {e}")
        return jsonify({'error': 'Failed to update role'}), 500

@admin_bp.route('/users/<int:user_id>/activate', methods=['PUT'])
@tenant_admin_required
def activate_user(user_id: int):
    return _set_user_active(user_id, True)

@admin_bp.route('/users/<int:user_id>/deactivate', methods=['PUT'])
@tenant_admin_required
def deactivate_user(user_id: int):
    return _set_user_active(user_id, False)

def _set_user_active(user_id: int, active: bool):
    tenant = get_current_tenant()
    user = User.query.filter_by(id=user_id, tenant_id=tenant.id).first_or_404()

    # Prevent deactivating self or last admin
    if user.id == current_user.id:
        return jsonify({'error': 'You cannot change activation status of your own account'}), 400
    if user.role in {'admin','super_admin'} and not active:
        admin_count = User.query.filter_by(tenant_id=tenant.id).filter(User.role.in_(['admin','super_admin'])).count()
        if admin_count <= 1:
            return jsonify({'error': 'Cannot deactivate the last admin of this tenant'}), 400

    user.is_active = active
    try:
        db.session.commit()
        status = 'activated' if active else 'deactivated'
        return jsonify({'message': f'User {status}', 'user': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to set activation: {e}")
        return jsonify({'error': 'Failed to update user status'}), 500

@admin_bp.route('/users/<int:user_id>/resend-verification', methods=['POST'])
@tenant_admin_required
def resend_verification(user_id: int):
    tenant = get_current_tenant()
    user = User.query.filter_by(id=user_id, tenant_id=tenant.id).first_or_404()

    if user.is_verified:
        return jsonify({'message': 'User is already verified'}), 200

    user.generate_verification_token()
    try:
        db.session.commit()
        _send_verification_email(user, tenant)
        return jsonify({'message': 'Verification email resent'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to resend verification: {e}")
        return jsonify({'error': 'Failed to resend verification'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@tenant_admin_required
def delete_user(user_id: int):
    tenant = get_current_tenant()
    user = User.query.filter_by(id=user_id, tenant_id=tenant.id).first_or_404()

    # Prevent deleting self or last admin
    if user.id == current_user.id:
        return jsonify({'error': 'You cannot delete your own account'}), 400
    if user.role in {'admin','super_admin'}:
        admin_count = User.query.filter_by(tenant_id=tenant.id).filter(User.role.in_(['admin','super_admin'])).count()
        if admin_count <= 1:
            return jsonify({'error': 'Cannot delete the last admin of this tenant'}), 400

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete user: {e}")
        return jsonify({'error': 'Failed to delete user'}), 500

# ============ Helpers ============

def _send_admin_invitation_email(invitation: AdminInvitation, tenant: Tenant):
    """Send an invitation email to a new admin."""
    try:
        # The base URL for the frontend application
        frontend_url = tenant.get_url().replace('http://', 'https://') 
        if 'localhost' in frontend_url:
            frontend_url = 'http://localhost:3000' # Adjust for local development
        
        accept_url = f"{frontend_url}/accept-invitation/{invitation.token}"
        
        msg = Message(
            subject=f"You're invited to manage {tenant.name}",
            recipients=[invitation.email],
            html=f'''
            <h2>You have been invited to join {tenant.name} as a {invitation.role}.</h2>
            <p>{invitation.invited_by.full_name} has invited you to help manage their hockey team.</p>
            <p>Please click the link below to create your account and accept the invitation:</p>
            <p><a href="{accept_url}">Accept Invitation</a></p>
            <p>This link will expire in 7 days.</p>
            '''
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send admin invitation email: {e}")

def _send_verification_email(user: User, tenant: Tenant):
    try:
        verify_url = f"{tenant.get_url()}/verify-email/{user.verification_token}"
        msg = Message(
            subject=f'Verify your email for {tenant.name}',
            recipients=[user.email],
            html=f'''
            <h2>Welcome to {tenant.name}!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verify_url}">Verify Email</a></p>
            <p>This link will expire in 7 days.</p>
            '''
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {e}")
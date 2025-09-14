"""
Tests for authentication system.
"""
import pytest
from datetime import datetime, timedelta
from app import create_app, db
from models.user import User
from models.tenant import Tenant

@pytest.fixture
def app():
    """Create test app with testing configuration."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def sample_tenant(app):
    """Create a sample tenant for testing."""
    with app.app_context():
        tenant = Tenant(
            name="Test Hockey Club",
            slug="test-hockey-club",
            subdomain="testhockey",
            is_active=True
        )
        db.session.add(tenant)
        db.session.commit()
        return tenant

@pytest.fixture
def sample_user(app, sample_tenant):
    """Create a sample user for testing."""
    with app.app_context():
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role="user",
            tenant_id=sample_tenant.id,
            is_verified=True
        )
        user.set_password("TestPassword123")
        db.session.add(user)
        db.session.commit()
        return user

class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, app, sample_tenant):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                email="newuser@example.com",
                first_name="New",
                last_name="User",
                tenant_id=sample_tenant.id
            )
            user.set_password("Password123")
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.email == "newuser@example.com"
            assert user.full_name == "New User"
            assert user.check_password("Password123")
            assert not user.check_password("wrongpassword")
    
    def test_password_hashing(self, app, sample_tenant):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(email="test@example.com", tenant_id=sample_tenant.id)
            user.set_password("TestPassword123")
            
            assert user.password_hash is not None
            assert user.password_hash != "TestPassword123"
            assert user.check_password("TestPassword123")
            assert not user.check_password("wrongpassword")
    
    def test_reset_token_generation(self, app, sample_user):
        """Test password reset token generation and verification."""
        with app.app_context():
            token = sample_user.generate_reset_token()
            
            assert token is not None
            assert sample_user.reset_token == token
            assert sample_user.reset_token_expires > datetime.utcnow()
            assert sample_user.verify_reset_token(token)
            assert not sample_user.verify_reset_token("invalid_token")
    
    def test_verification_token_generation(self, app, sample_user):
        """Test email verification token generation."""
        with app.app_context():
            token = sample_user.generate_verification_token()
            
            assert token is not None
            assert sample_user.verification_token == token
            assert sample_user.verification_token_expires > datetime.utcnow()
    
    def test_user_permissions(self, app, sample_tenant):
        """Test user permission system."""
        with app.app_context():
            # Regular user
            user = User(email="user@example.com", role="user", tenant_id=sample_tenant.id)
            assert user.has_permission("view_own_data")
            assert not user.has_permission("manage_players")
            assert not user.is_admin
            
            # Admin user
            admin = User(email="admin@example.com", role="admin", tenant_id=sample_tenant.id)
            assert admin.has_permission("view_own_data")
            assert admin.has_permission("manage_players")
            assert admin.is_admin
            assert not admin.is_super_admin
            
            # Super admin
            super_admin = User(email="super@example.com", role="super_admin", tenant_id=sample_tenant.id)
            assert super_admin.has_permission("view_own_data")
            assert super_admin.has_permission("manage_players")
            assert super_admin.has_permission("any_permission")
            assert super_admin.is_admin
            assert super_admin.is_super_admin

class TestAuthenticationAPI:
    """Test authentication API endpoints."""
    
    def test_user_registration(self, client, sample_tenant):
        """Test user registration endpoint."""
        with client.application.test_request_context('/', base_url=f'http://testhockey.localhost:5000'):
            data = {
                'email': 'newuser@example.com',
                'password': 'TestPassword123',
                'first_name': 'New',
                'last_name': 'User'
            }
            
            response = client.post('/api/auth/register', json=data)
            assert response.status_code == 201
            
            result = response.get_json()
            assert result['message'] == 'User registered successfully'
            assert result['user']['email'] == 'newuser@example.com'
            assert result['user']['role'] == 'admin'  # First user becomes admin
            assert result['user']['is_verified'] is True
    
    def test_user_registration_duplicate_email(self, client, sample_user):
        """Test registration with duplicate email."""
        with client.application.test_request_context('/', base_url=f'http://testhockey.localhost:5000'):
            data = {
                'email': 'test@example.com',  # Same as sample_user
                'password': 'TestPassword123'
            }
            
            response = client.post('/api/auth/register', json=data)
            assert response.status_code == 409
            
            result = response.get_json()
            assert 'already exists' in result['error']
    
    def test_user_registration_weak_password(self, client, sample_tenant):
        """Test registration with weak password."""
        with client.application.test_request_context('/', base_url=f'http://testhockey.localhost:5000'):
            data = {
                'email': 'newuser@example.com',
                'password': 'weak'  # Too weak
            }
            
            response = client.post('/api/auth/register', json=data)
            assert response.status_code == 400
            
            result = response.get_json()
            assert 'Password must be at least 8 characters' in result['error']
    
    def test_user_login_success(self, client, sample_user):
        """Test successful user login."""
        with client.application.test_request_context('/', base_url=f'http://testhockey.localhost:5000'):
            data = {
                'email': 'test@example.com',
                'password': 'TestPassword123'
            }
            
            response = client.post('/api/auth/login', json=data)
            assert response.status_code == 200
            
            result = response.get_json()
            assert result['message'] == 'Login successful'
            assert result['user']['email'] == 'test@example.com'
            assert 'tenant' in result
    
    def test_user_login_invalid_credentials(self, client, sample_user):
        """Test login with invalid credentials."""
        with client.application.test_request_context('/', base_url=f'http://testhockey.localhost:5000'):
            data = {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }
            
            response = client.post('/api/auth/login', json=data)
            assert response.status_code == 401
            
            result = response.get_json()
            assert 'Invalid email or password' in result['error']
    
    def test_user_login_inactive_account(self, client, sample_user):
        """Test login with inactive account."""
        with client.application.test_request_context('/', base_url=f'http://testhockey.localhost:5000'):
            # Deactivate user
            sample_user.is_active = False
            db.session.commit()
            
            data = {
                'email': 'test@example.com',
                'password': 'TestPassword123'
            }
            
            response = client.post('/api/auth/login', json=data)
            assert response.status_code == 403
            
            result = response.get_json()
            assert 'Account is deactivated' in result['error']
    
    def test_password_reset_request(self, client, sample_user):
        """Test password reset request."""
        with client.application.test_request_context('/', base_url=f'http://testhockey.localhost:5000'):
            data = {'email': 'test@example.com'}
            
            response = client.post('/api/auth/forgot-password', json=data)
            assert response.status_code == 200
            
            result = response.get_json()
            assert 'reset link has been sent' in result['message']
    
    def test_password_reset_with_token(self, client, sample_user):
        """Test password reset with valid token."""
        with client.application.app_context():
            token = sample_user.generate_reset_token()
            db.session.commit()
            
            data = {
                'token': token,
                'password': 'NewPassword123'
            }
            
            response = client.post('/api/auth/reset-password', json=data)
            assert response.status_code == 200
            
            result = response.get_json()
            assert result['message'] == 'Password reset successfully'
            
            # Verify password was changed
            assert sample_user.check_password('NewPassword123')
            assert not sample_user.check_password('TestPassword123')
    
    def test_email_verification(self, client, sample_user):
        """Test email verification with token."""
        with client.application.app_context():
            token = sample_user.generate_verification_token()
            sample_user.is_verified = False
            db.session.commit()
            
            response = client.post(f'/api/auth/verify-email/{token}')
            assert response.status_code == 200
            
            result = response.get_json()
            assert result['message'] == 'Email verified successfully'
            
            # Verify user is now verified
            db.session.refresh(sample_user)
            assert sample_user.is_verified is True

class TestAuthenticationValidation:
    """Test authentication validation functions."""
    
    def test_email_validation(self):
        """Test email format validation."""
        from routes.auth import is_valid_email
        
        # Valid emails
        assert is_valid_email("test@example.com") is True
        assert is_valid_email("user.name@domain.co.uk") is True
        assert is_valid_email("test+tag@example.org") is True
        
        # Invalid emails
        assert is_valid_email("invalid") is False
        assert is_valid_email("@example.com") is False
        assert is_valid_email("test@") is False
        assert is_valid_email("test.example.com") is False
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        from routes.auth import is_strong_password
        
        # Strong passwords
        is_strong, _ = is_strong_password("TestPassword123")
        assert is_strong is True
        
        is_strong, _ = is_strong_password("MySecure123!")
        assert is_strong is True
        
        # Weak passwords
        is_strong, message = is_strong_password("weak")
        assert is_strong is False
        assert "at least 8 characters" in message
        
        is_strong, message = is_strong_password("nouppercase123")
        assert is_strong is False
        assert "uppercase letter" in message
        
        is_strong, message = is_strong_password("NOLOWERCASE123")
        assert is_strong is False
        assert "lowercase letter" in message
        
        is_strong, message = is_strong_password("NoNumbers")
        assert is_strong is False
        assert "number" in message

"""
Tests for tenant onboarding and registration flow.
"""
import pytest
from app import create_app, db
from models.tenant import Tenant
from models.user import User
from routes.tenant_onboarding import onboarding_bp
from utils.onboarding_helpers import (
    validate_subdomain_format, 
    suggest_subdomains,
    generate_onboarding_checklist,
    calculate_setup_progress
)

@pytest.fixture
def app():
    """Create test app with onboarding routes."""
    app = create_app('testing')
    app.register_blueprint(onboarding_bp, url_prefix='/api/onboarding')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

class TestTenantRegistration:
    """Test tenant registration functionality."""
    
    def test_check_availability_valid_data(self, client):
        """Test availability check with valid data."""
        data = {
            'organization_name': 'Test Hockey Club',
            'preferred_subdomain': 'testhockey'
        }
        
        response = client.post('/api/onboarding/check-availability', json=data)
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['organization_name']['available'] is True
        assert result['subdomain']['available'] is True
    
    def test_check_availability_duplicate_subdomain(self, client):
        """Test availability check with existing subdomain."""
        # Create existing tenant
        tenant = Tenant(
            name="Existing Club",
            slug="existing-club",
            subdomain="existing",
            is_active=True
        )
        db.session.add(tenant)
        db.session.commit()
        
        data = {
            'organization_name': 'New Hockey Club',
            'preferred_subdomain': 'existing'
        }
        
        response = client.post('/api/onboarding/check-availability', json=data)
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['subdomain']['available'] is False
        assert 'already taken' in result['subdomain']['message']
        assert len(result['subdomain']['suggestions']) > 0
    
    def test_check_availability_invalid_subdomain(self, client):
        """Test availability check with invalid subdomain format."""
        data = {
            'organization_name': 'Test Hockey Club',
            'preferred_subdomain': 'invalid-subdomain-'  # Ends with hyphen
        }
        
        response = client.post('/api/onboarding/check-availability', json=data)
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['subdomain']['available'] is False
    
    def test_register_tenant_success(self, client):
        """Test successful tenant registration."""
        data = {
            'organization_name': 'New Hockey Club',
            'subdomain': 'newhockey',
            'admin_email': 'admin@newhockey.com',
            'admin_password': 'SecurePass123',
            'admin_first_name': 'John',
            'admin_last_name': 'Admin'
        }
        
        response = client.post('/api/onboarding/register', json=data)
        assert response.status_code == 201
        
        result = response.get_json()
        assert result['message'] == 'Organization registered successfully'
        assert result['tenant']['name'] == 'New Hockey Club'
        assert result['tenant']['subdomain'] == 'newhockey'
        assert result['admin_user']['email'] == 'admin@newhockey.com'
        assert result['admin_user']['role'] == 'admin'
        
        # Verify tenant was created in database
        tenant = Tenant.query.filter_by(subdomain='newhockey').first()
        assert tenant is not None
        assert tenant.name == 'New Hockey Club'
        
        # Verify admin user was created
        admin = User.query.filter_by(email='admin@newhockey.com').first()
        assert admin is not None
        assert admin.role == 'admin'
        assert admin.is_verified is True
        assert admin.tenant_id == tenant.id
    
    def test_register_tenant_duplicate_subdomain(self, client):
        """Test registration with duplicate subdomain."""
        # Create existing tenant
        existing_tenant = Tenant(
            name="Existing Club",
            slug="existing-club", 
            subdomain="existing",
            is_active=True
        )
        db.session.add(existing_tenant)
        db.session.commit()
        
        data = {
            'organization_name': 'New Hockey Club',
            'subdomain': 'existing',  # Duplicate
            'admin_email': 'admin@new.com',
            'admin_password': 'SecurePass123',
            'admin_first_name': 'John',
            'admin_last_name': 'Admin'
        }
        
        response = client.post('/api/onboarding/register', json=data)
        assert response.status_code == 400
        
        result = response.get_json()
        assert 'already taken' in str(result['errors'])
    
    def test_register_tenant_weak_password(self, client):
        """Test registration with weak password."""
        data = {
            'organization_name': 'New Hockey Club',
            'subdomain': 'newhockey',
            'admin_email': 'admin@newhockey.com',
            'admin_password': 'weak',  # Too weak
            'admin_first_name': 'John',
            'admin_last_name': 'Admin'
        }
        
        response = client.post('/api/onboarding/register', json=data)
        assert response.status_code == 400
        
        result = response.get_json()
        assert any('Password must be at least 8 characters' in error for error in result['errors'])
    
    def test_register_tenant_missing_fields(self, client):
        """Test registration with missing required fields."""
        data = {
            'organization_name': 'New Hockey Club',
            # Missing subdomain, admin_email, etc.
        }
        
        response = client.post('/api/onboarding/register', json=data)
        assert response.status_code == 400
        
        result = response.get_json()
        assert len(result['errors']) > 0

class TestOnboardingStatus:
    """Test onboarding status tracking."""
    
    def test_get_onboarding_status_new_tenant(self, client):
        """Test onboarding status for new tenant."""
        # Create tenant with admin
        tenant = Tenant(
            name="Test Club",
            slug="test-club",
            subdomain="testclub",
            is_active=True
        )
        db.session.add(tenant)
        db.session.flush()
        
        admin = User(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_verified=True,
            tenant_id=tenant.id
        )
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()
        
        response = client.get(f'/api/onboarding/onboarding-status/{tenant.subdomain}')
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['tenant']['name'] == 'Test Club'
        assert result['onboarding_steps']['admin_user_created'] is True
        assert result['onboarding_steps']['players_added'] is False
        assert result['completion_percentage'] > 0
    
    def test_get_onboarding_status_nonexistent_tenant(self, client):
        """Test onboarding status for nonexistent tenant."""
        response = client.get('/api/onboarding/onboarding-status/nonexistent')
        assert response.status_code == 404

class TestOnboardingHelpers:
    """Test onboarding helper functions."""
    
    def test_validate_subdomain_format_valid(self):
        """Test subdomain validation with valid formats."""
        valid_subdomains = ['test', 'test123', 'test-club', 'hockey2024']
        
        for subdomain in valid_subdomains:
            is_valid, message = validate_subdomain_format(subdomain)
            assert is_valid is True, f"'{subdomain}' should be valid"
    
    def test_validate_subdomain_format_invalid(self):
        """Test subdomain validation with invalid formats."""
        invalid_subdomains = [
            '',  # Empty
            'ab',  # Too short
            'test-',  # Ends with hyphen
            '-test',  # Starts with hyphen
            'test_club',  # Contains underscore
            'TEST',  # Uppercase
            'www',  # Reserved
        ]
        
        for subdomain in invalid_subdomains:
            is_valid, message = validate_subdomain_format(subdomain)
            assert is_valid is False, f"'{subdomain}' should be invalid"
    
    def test_suggest_subdomains(self):
        """Test subdomain suggestion generation."""
        suggestions = suggest_subdomains('Test Hockey Club', count=3)
        
        assert len(suggestions) <= 3
        for suggestion in suggestions:
            is_valid, _ = validate_subdomain_format(suggestion)
            assert is_valid is True
    
    def test_generate_onboarding_checklist(self, app):
        """Test onboarding checklist generation."""
        with app.app_context():
            # Create test tenant
            tenant = Tenant(
                name="Test Club",
                slug="test-club",
                subdomain="testclub",
                is_active=True
            )
            db.session.add(tenant)
            db.session.flush()
            
            checklist = generate_onboarding_checklist(tenant.id)
            
            assert 'checklist' in checklist
            assert 'completion_percentage' in checklist
            assert len(checklist['checklist']) > 0
            
            # All items should have required fields
            for item in checklist['checklist']:
                assert 'id' in item
                assert 'title' in item
                assert 'completed' in item
                assert 'required' in item
    
    def test_calculate_setup_progress(self, app):
        """Test setup progress calculation."""
        with app.app_context():
            # Create test tenant with admin
            tenant = Tenant(
                name="Test Club",
                slug="test-club", 
                subdomain="testclub",
                is_active=True
            )
            db.session.add(tenant)
            db.session.flush()
            
            admin = User(
                email="admin@test.com",
                first_name="Admin",
                last_name="User",
                role="admin",
                tenant_id=tenant.id
            )
            admin.set_password("password123")
            db.session.add(admin)
            db.session.commit()
            
            progress = calculate_setup_progress(tenant.id)
            
            assert 'overall_percentage' in progress
            assert 'categories' in progress
            assert progress['overall_percentage'] > 0  # Should have some progress with admin user
            
            # Check category structure
            for category in progress['categories'].values():
                assert 'name' in category
                assert 'percentage' in category
                assert 'items' in category

class TestWelcomeEmail:
    """Test welcome email functionality."""
    
    def test_send_welcome_email_success(self, client):
        """Test sending welcome email."""
        # Create tenant with admin
        tenant = Tenant(
            name="Test Club",
            slug="test-club",
            subdomain="testclub",
            is_active=True
        )
        db.session.add(tenant)
        db.session.flush()
        
        admin = User(
            email="admin@test.com",
            first_name="Admin",
            last_name="User", 
            role="admin",
            tenant_id=tenant.id
        )
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()
        
        data = {'tenant_id': tenant.id}
        response = client.post('/api/onboarding/welcome-email', json=data)
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['message'] == 'Welcome email sent successfully'
        assert result['recipient'] == 'admin@test.com'
    
    def test_send_welcome_email_invalid_tenant(self, client):
        """Test sending welcome email with invalid tenant."""
        data = {'tenant_id': 999}
        response = client.post('/api/onboarding/welcome-email', json=data)
        assert response.status_code == 404

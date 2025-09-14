"""
Tests for tenant routing and multi-tenant functionality.
"""
import pytest
from app import create_app, db
from models.tenant import Tenant
from utils.tenant import get_current_tenant

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

class TestTenantModel:
    """Test tenant model functionality."""
    
    def test_tenant_creation(self, app):
        """Test creating a new tenant."""
        with app.app_context():
            tenant = Tenant(
                name="Sample Club",
                slug="sample-club",
                subdomain="sample"
            )
            db.session.add(tenant)
            db.session.commit()
            
            assert tenant.id is not None
            assert tenant.name == "Sample Club"
            assert tenant.slug == "sample-club"
            assert tenant.subdomain == "sample"
            assert tenant.is_active is True
    
    def test_slug_generation(self):
        """Test automatic slug generation."""
        slug = Tenant.generate_slug("My Hockey Club!")
        assert slug == "my-hockey-club"
        
        slug = Tenant.generate_slug("  Test   Club  ")
        assert slug == "test-club"
    
    def test_subdomain_validation(self):
        """Test subdomain validation."""
        assert Tenant.is_valid_subdomain("test") is True
        assert Tenant.is_valid_subdomain("test-club") is True
        assert Tenant.is_valid_subdomain("test123") is True
        assert Tenant.is_valid_subdomain("") is True  # Optional
        assert Tenant.is_valid_subdomain(None) is True  # Optional
        
        # Invalid cases
        assert Tenant.is_valid_subdomain("te") is False  # Too short
        assert Tenant.is_valid_subdomain("-test") is False  # Starts with hyphen
        assert Tenant.is_valid_subdomain("test-") is False  # Ends with hyphen
        assert Tenant.is_valid_subdomain("TEST") is False  # Uppercase
        assert Tenant.is_valid_subdomain("test_club") is False  # Underscore
    
    def test_tenant_url_generation(self, app, sample_tenant):
        """Test tenant URL generation."""
        with app.app_context():
            # Test subdomain URL
            app.config['TENANT_URL_SUBDOMAIN_ENABLED'] = True
            app.config['SERVER_NAME'] = 'example.com'
            
            url = sample_tenant.get_url()
            assert url == "http://testhockey.example.com"
            
            # Test path-based URL
            app.config['TENANT_URL_SUBDOMAIN_ENABLED'] = False
            app.config['TENANT_URL_PATH_ENABLED'] = True
            
            url = sample_tenant.get_url()
            assert url == "http://example.com/test-hockey-club"

class TestTenantRouting:
    """Test tenant routing functionality."""
    
    def test_subdomain_tenant_identification(self, app, sample_tenant):
        """Test tenant identification via subdomain."""
        with app.test_request_context('/', base_url='http://testhockey.localhost:5000'):
            app.config['TENANT_URL_SUBDOMAIN_ENABLED'] = True
            
            from utils.tenant import get_current_tenant
            tenant = get_current_tenant()
            
            assert tenant is not None
            assert tenant.id == sample_tenant.id
    
    def test_path_tenant_identification(self, app, sample_tenant):
        """Test tenant identification via path."""
        with app.test_request_context('/test-hockey-club/dashboard'):
            app.config['TENANT_URL_SUBDOMAIN_ENABLED'] = False
            app.config['TENANT_URL_PATH_ENABLED'] = True
            
            from utils.tenant import get_current_tenant
            tenant = get_current_tenant()
            
            assert tenant is not None
            assert tenant.id == sample_tenant.id
    
    def test_no_tenant_found(self, app):
        """Test behavior when no tenant is found."""
        with app.test_request_context('/', base_url='http://nonexistent.localhost:5000'):
            from utils.tenant import get_current_tenant
            tenant = get_current_tenant()
            
            assert tenant is None

class TestTenantAPI:
    """Test tenant API endpoints."""
    
    def test_tenant_registration(self, client):
        """Test tenant registration endpoint."""
        data = {
            'name': 'New Hockey Club',
            'subdomain': 'newhockey',
            'position_mode': 'three_position'
        }
        
        response = client.post('/api/tenant/register', json=data)
        assert response.status_code == 201
        
        result = response.get_json()
        assert result['message'] == 'Tenant registered successfully'
        assert result['tenant']['name'] == 'New Hockey Club'
        assert result['tenant']['subdomain'] == 'newhockey'
        assert result['tenant']['slug'] == 'new-hockey-club'
    
    def test_tenant_registration_duplicate_name(self, client, sample_tenant):
        """Test tenant registration with duplicate name."""
        data = {
            'name': 'Test Hockey Club',  # Same as sample_tenant
            'subdomain': 'different'
        }
        
        response = client.post('/api/tenant/register', json=data)
        assert response.status_code == 409
        
        result = response.get_json()
        assert 'already exists' in result['error']
    
    def test_tenant_registration_duplicate_subdomain(self, client, sample_tenant):
        """Test tenant registration with duplicate subdomain."""
        data = {
            'name': 'Different Club',
            'subdomain': 'testhockey'  # Same as sample_tenant
        }
        
        response = client.post('/api/tenant/register', json=data)
        assert response.status_code == 409
        
        result = response.get_json()
        assert 'already taken' in result['error']
    
    def test_check_availability(self, client, sample_tenant):
        """Test availability checking endpoint."""
        # Check available name
        data = {'name': 'Available Club'}
        response = client.post('/api/tenant/check-availability', json=data)
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['name_available'] is True
        assert result['generated_slug'] == 'available-club'
        
        # Check unavailable name
        data = {'name': 'Test Hockey Club'}
        response = client.post('/api/tenant/check-availability', json=data)
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['name_available'] is False
        
        # Check subdomain availability
        data = {'subdomain': 'available'}
        response = client.post('/api/tenant/check-availability', json=data)
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['subdomain_available'] is True
        assert result['subdomain_valid'] is True
        
        # Check unavailable subdomain
        data = {'subdomain': 'testhockey'}
        response = client.post('/api/tenant/check-availability', json=data)
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['subdomain_available'] is False
        assert result['subdomain_valid'] is True

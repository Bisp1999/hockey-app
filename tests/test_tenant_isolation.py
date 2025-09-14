"""
Tests for tenant isolation middleware and automatic query filtering.
"""
import pytest
from flask import g
from app import create_app, db
from models.tenant import Tenant
from models.user import User
from models.player import Player
from models.game import Game
from utils.tenant import set_tenant_context, get_current_tenant_id
from utils.tenant_isolation import TenantIsolationMiddleware, validate_tenant_access

@pytest.fixture
def app():
    """Create test app with tenant isolation."""
    app = create_app('testing')
    
    # Initialize tenant isolation middleware
    isolation_middleware = TenantIsolationMiddleware(app, db)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def tenants(app):
    """Create test tenants."""
    with app.app_context():
        tenant1 = Tenant(
            name="Tenant 1 Hockey Club",
            slug="tenant1",
            subdomain="tenant1",
            is_active=True
        )
        tenant2 = Tenant(
            name="Tenant 2 Hockey Club", 
            slug="tenant2",
            subdomain="tenant2",
            is_active=True
        )
        db.session.add_all([tenant1, tenant2])
        db.session.commit()
        return tenant1, tenant2

@pytest.fixture
def users(app, tenants):
    """Create test users for different tenants."""
    tenant1, tenant2 = tenants
    with app.app_context():
        user1 = User(
            email="user1@tenant1.com",
            first_name="User",
            last_name="One",
            tenant_id=tenant1.id,
            is_verified=True
        )
        user1.set_password("password123")
        
        user2 = User(
            email="user2@tenant2.com",
            first_name="User", 
            last_name="Two",
            tenant_id=tenant2.id,
            is_verified=True
        )
        user2.set_password("password123")
        
        db.session.add_all([user1, user2])
        db.session.commit()
        return user1, user2

class TestTenantIsolation:
    """Test tenant isolation functionality."""
    
    def test_automatic_tenant_assignment(self, app, tenants):
        """Test that new objects get tenant_id automatically assigned."""
        tenant1, tenant2 = tenants
        
        with app.app_context():
            # Set tenant context
            set_tenant_context(tenant1)
            
            # Create a player without explicitly setting tenant_id
            player = Player(
                name="Test Player",
                email="player@test.com",
                position="forward",
                player_type="regular"
            )
            db.session.add(player)
            db.session.flush()  # Trigger before_flush event
            
            # Should have tenant_id automatically assigned
            assert player.tenant_id == tenant1.id
    
    def test_query_filtering_by_tenant(self, app, tenants, users):
        """Test that queries are automatically filtered by tenant."""
        tenant1, tenant2 = tenants
        user1, user2 = users
        
        with app.app_context():
            # Create players for different tenants
            player1 = Player(
                name="Player 1",
                email="player1@test.com",
                position="forward",
                player_type="regular",
                tenant_id=tenant1.id
            )
            player2 = Player(
                name="Player 2", 
                email="player2@test.com",
                position="defence",
                player_type="regular",
                tenant_id=tenant2.id
            )
            db.session.add_all([player1, player2])
            db.session.commit()
            
            # Set tenant 1 context
            set_tenant_context(tenant1)
            
            # Query should only return tenant 1 players
            players = Player.query.all()
            assert len(players) == 1
            assert players[0].id == player1.id
            assert players[0].tenant_id == tenant1.id
            
            # Set tenant 2 context
            set_tenant_context(tenant2)
            
            # Query should only return tenant 2 players
            players = Player.query.all()
            assert len(players) == 1
            assert players[0].id == player2.id
            assert players[0].tenant_id == tenant2.id
    
    def test_cross_tenant_access_prevention(self, app, tenants):
        """Test that cross-tenant access is prevented."""
        tenant1, tenant2 = tenants
        
        with app.app_context():
            # Create player in tenant 1
            set_tenant_context(tenant1)
            player1 = Player(
                name="Player 1",
                email="player1@test.com", 
                position="forward",
                player_type="regular",
                tenant_id=tenant1.id
            )
            db.session.add(player1)
            db.session.commit()
            player1_id = player1.id
            
            # Switch to tenant 2 context
            set_tenant_context(tenant2)
            
            # Try to access player from tenant 1
            player = Player.query.get(player1_id)
            assert player is None  # Should not be accessible
    
    def test_bulk_operations_tenant_filtering(self, app, tenants):
        """Test that bulk operations are filtered by tenant."""
        tenant1, tenant2 = tenants
        
        with app.app_context():
            # Create players for both tenants
            players = []
            for i, tenant in enumerate([tenant1, tenant2], 1):
                for j in range(3):
                    player = Player(
                        name=f"Player {i}-{j}",
                        email=f"player{i}{j}@test.com",
                        position="forward",
                        player_type="regular",
                        tenant_id=tenant.id
                    )
                    players.append(player)
            
            db.session.add_all(players)
            db.session.commit()
            
            # Set tenant 1 context
            set_tenant_context(tenant1)
            
            # Bulk update should only affect tenant 1 players
            Player.query.update({'position': 'defence'})
            db.session.commit()
            
            # Check that only tenant 1 players were updated
            tenant1_players = Player.query.filter_by(tenant_id=tenant1.id).all()
            tenant2_players = Player.query.filter_by(tenant_id=tenant2.id).all()
            
            for player in tenant1_players:
                assert player.position == 'defence'
            
            for player in tenant2_players:
                assert player.position == 'forward'  # Should remain unchanged
    
    def test_tenant_mixin_methods(self, app, tenants):
        """Test TenantMixin helper methods."""
        tenant1, tenant2 = tenants
        
        with app.app_context():
            set_tenant_context(tenant1)
            
            # Test create_for_tenant
            player = Player.create_for_tenant(
                name="Test Player",
                email="test@example.com",
                position="forward",
                player_type="regular"
            )
            assert player.tenant_id == tenant1.id
            
            # Test query_for_tenant
            player.save()
            
            # Create player for tenant 2
            player2 = Player(
                name="Player 2",
                email="player2@example.com",
                position="defence", 
                player_type="regular",
                tenant_id=tenant2.id
            )
            db.session.add(player2)
            db.session.commit()
            
            # Query for tenant should only return tenant 1 players
            tenant1_players = Player.query_for_tenant(tenant1.id).all()
            assert len(tenant1_players) == 1
            assert tenant1_players[0].tenant_id == tenant1.id
    
    def test_validate_tenant_access(self, app, tenants):
        """Test tenant access validation."""
        tenant1, tenant2 = tenants
        
        with app.app_context():
            # Create player in tenant 1
            player = Player(
                name="Test Player",
                email="test@example.com",
                position="forward",
                player_type="regular", 
                tenant_id=tenant1.id
            )
            db.session.add(player)
            db.session.commit()
            
            # Set tenant 1 context - should have access
            set_tenant_context(tenant1)
            assert validate_tenant_access(player) is True
            
            # Set tenant 2 context - should not have access
            set_tenant_context(tenant2)
            assert validate_tenant_access(player) is False
    
    def test_middleware_request_hooks(self, app, tenants):
        """Test middleware request hooks."""
        tenant1, tenant2 = tenants
        
        with app.test_request_context('/', base_url=f'http://{tenant1.subdomain}.localhost:5000'):
            # Simulate before_request
            from utils.tenant_isolation import TenantIsolationMiddleware
            middleware = TenantIsolationMiddleware()
            middleware.before_request()
            
            # Should have tenant context set
            current_tenant_id = get_current_tenant_id()
            assert current_tenant_id == tenant1.id
    
    def test_skip_tenant_detection_paths(self, app):
        """Test that certain paths skip tenant detection."""
        from utils.tenant_isolation import TenantIsolationMiddleware
        middleware = TenantIsolationMiddleware()
        
        with app.test_request_context('/health'):
            assert middleware.should_skip_tenant_detection() is True
        
        with app.test_request_context('/api/tenants/register'):
            assert middleware.should_skip_tenant_detection() is True
        
        with app.test_request_context('/api/auth/login'):
            assert middleware.should_skip_tenant_detection() is False

class TestModelTenantIsolation:
    """Test tenant isolation on specific models."""
    
    def test_user_tenant_isolation(self, app, tenants):
        """Test User model tenant isolation."""
        tenant1, tenant2 = tenants
        
        with app.app_context():
            # Create users for different tenants
            user1 = User(
                email="user1@test.com",
                first_name="User",
                last_name="One", 
                tenant_id=tenant1.id
            )
            user1.set_password("password123")
            
            user2 = User(
                email="user2@test.com",
                first_name="User",
                last_name="Two",
                tenant_id=tenant2.id
            )
            user2.set_password("password123")
            
            db.session.add_all([user1, user2])
            db.session.commit()
            
            # Set tenant context and verify isolation
            set_tenant_context(tenant1)
            users = User.query.all()
            assert len(users) == 1
            assert users[0].id == user1.id
    
    def test_game_tenant_isolation(self, app, tenants):
        """Test Game model tenant isolation.""" 
        tenant1, tenant2 = tenants
        
        with app.app_context():
            from datetime import date, time
            
            # Create games for different tenants
            game1 = Game(
                date=date.today(),
                time=time(19, 0),
                venue="Rink 1",
                tenant_id=tenant1.id
            )
            game2 = Game(
                date=date.today(),
                time=time(20, 0), 
                venue="Rink 2",
                tenant_id=tenant2.id
            )
            
            db.session.add_all([game1, game2])
            db.session.commit()
            
            # Set tenant context and verify isolation
            set_tenant_context(tenant1)
            games = Game.query.all()
            assert len(games) == 1
            assert games[0].id == game1.id

import pytest
import os
from app import create_app, db # db is defined in app/__init__
from app.models import User, Role # Assuming Role is needed for admin setup

@pytest.fixture(scope='module')
def test_app():
    # Set environment variables for testing *before* create_app() is called
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    # For other configurations, we'll set them directly on app.config after creation
    # if create_app doesn't pick them up from prefixed env vars automatically.

    app = create_app()

    # Now apply other test-specific configurations
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for simpler form tests
    # SECRET_KEY is already handled by create_app, can be overridden if needed:
    # app.config['SECRET_KEY'] = 'test_secret_key'

    with app.app_context():
        db.create_all() # Create tables in the in-memory database
        
        # Optional: Create a default admin role if needed by other tests or app logic
        # This helps ensure the '/register' route protection test can run reliably.
        admin_role_name = 'admin'
        admin_role = Role.query.filter_by(name=admin_role_name).first()
        if not admin_role:
            admin_role = Role(name=admin_role_name)
            db.session.add(admin_role)
            db.session.commit()
        
        yield app # provide the app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    """A test client for the app."""
    return test_app.test_client()

# Test 1: App Creation
def test_app_creation(test_app):
    assert test_app is not None
    assert test_app.config['TESTING'] is True
    assert test_app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    assert test_app.config['WTF_CSRF_ENABLED'] is False

# Test 2: Login Page Accessibility
def test_login_page_loads(test_client):
    response = test_client.get('/login')
    assert response.status_code == 200
    # Check for some text expected on the login page
    # Assuming the login page has a form with a submit button "Войти"
    assert "Войти" in response.data.decode('utf-8')

# Test 3: Basic Model Creation (Role)
def test_role_creation(test_app): # Needs app context
    with test_app.app_context(): # Ensure app context for db operations
        # The 'admin' role should have been created by the test_app fixture
        role = Role.query.filter_by(name='admin').first()
        assert role is not None
        assert role.name == 'admin'
        
        editor_role_name = 'editor'
        new_role = Role(name=editor_role_name)
        db.session.add(new_role)
        db.session.commit()
        
        fetched_editor_role = Role.query.filter_by(name=editor_role_name).first()
        assert fetched_editor_role is not None
        assert fetched_editor_role.name == editor_role_name

# Test 4: Register Route Protection
# For this test, we need generate_password_hash
from werkzeug.security import generate_password_hash

def test_register_route_protection_when_admin_exists(test_client, test_app):
    with test_app.app_context():
        # Ensure an admin role exists (should be handled by test_app fixture)
        admin_role = Role.query.filter_by(name='admin').first()
        assert admin_role is not None, "Admin role should exist from fixture setup"

        # Check if an admin user already exists
        existing_admin_user = User.query.join(Role).filter(Role.name == 'admin').first()
        if not existing_admin_user:
            # Create an admin user if one doesn't exist, for the purpose of this test
            hashed_password = generate_password_hash('adminpass')
            # Ensure to use role_id for assignment
            admin_user = User(username='testadmin', email='admin@test.com', password_hash=hashed_password, role_id=admin_role.id)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user created for test: {admin_user.username} with role ID {admin_role.id}")
        else:
            print(f"Admin user already exists: {existing_admin_user.username}")


        # Now, try to access the /register route
        response = test_client.get('/register')
        
        # Print response data for debugging if the assert fails
        if response.status_code != 302:
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Data: {response.data.decode('utf-8', 'ignore')}")

        assert response.status_code == 302, "Accessing /register when admin exists should redirect."
        # Check if the redirect location is as expected (e.g., to '/login')
        # The actual redirect URL might depend on url_for behavior in test context
        # For now, let's assume it redirects to '/login' or contains '/login'
        assert '/login' in response.location, f"Redirect location was {response.location}, expected '/login'"
        
        # To check flash messages, you'd typically need session handling configured
        # and follow redirects. For simplicity, checking redirect location is often enough.
        # If you want to check flash message, you might do:
        # response = test_client.get('/register', follow_redirects=True)
        # assert b'Регистрация нового администратора невозможна' in response.data
        # However, this makes the test more complex. The redirect itself is a strong indicator.

# Test 5: Ensure /register route is accessible if NO admin exists
@pytest.fixture(scope='module')
def test_app_no_admin():
    # A separate app fixture to ensure no admin user exists initially for this specific test
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:' # Fresh in-memory DB
    app_no_admin = create_app()
    app_no_admin.config['TESTING'] = True
    app_no_admin.config['WTF_CSRF_ENABLED'] = False
    app_no_admin.config['SECRET_KEY'] = 'test_secret_key_no_admin'


    with app_no_admin.app_context():
        db.create_all()
        # DO NOT create an admin user here.
        # We might need the 'admin' role for the form, but no user assigned to it.
        admin_role_name = 'admin' # The role itself might be needed by RegisterForm
        admin_role = Role.query.filter_by(name=admin_role_name).first()
        if not admin_role:
            admin_role = Role(name=admin_role_name)
            db.session.add(admin_role)
            # Also, create other roles if RegisterForm expects them for its choices
            user_role = Role(name='user') # Example
            db.session.add(user_role)
            db.session.commit()

        yield app_no_admin
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def test_client_no_admin(test_app_no_admin):
    return test_app_no_admin.test_client()

def test_register_route_accessible_if_no_admin(test_client_no_admin, test_app_no_admin):
     # Ensure no admin user exists (this fixture's purpose)
    with test_app_no_admin.app_context():
        admin_user = User.query.join(Role).filter(Role.name == 'admin').first()
        assert admin_user is None, "For this test, no admin user should exist initially."

    response = test_client_no_admin.get('/register')
    assert response.status_code == 200
    assert "Регистрация администратора" in response.data.decode('utf-8') # Check for title or key text
    # Check that the warning flash message is NOT present
    assert 'Регистрация нового администратора невозможна' not in response.data.decode('utf-8')

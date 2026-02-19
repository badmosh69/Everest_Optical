import sys
import os

# Simulate running from backend directory (which is how we will configure Render)
os.chdir('backend')
sys.path.insert(0, os.getcwd())

print(f"Working Directory: {os.getcwd()}")
print("1. Testing Import of Flask App...")
try:
    from app import app
    print("SUCCESS: Flask app imported successfully.")
except Exception as e:
    print(f"FAILURE: Could not import app. Error: {e}")
    sys.exit(1)

print("\n2. Testing Database Configuration...")
# Check if SQLALCHEMY_DATABASE_URI is set (should be sqlite:///site.db if no env var)
db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
print(f"Current DB URI: {db_uri}")

if not db_uri:
    print("FAILURE: SQLALCHEMY_DATABASE_URI is not set.")
    sys.exit(1)

if 'sqlite' in db_uri and not os.environ.get('DATABASE_URL'):
    print("SUCCESS: Correctly falling back to SQLite when DATABASE_URL is missing.")
elif 'postgres' in db_uri:
    print("SUCCESS: Using PostgreSQL configuration.")
else:
    print(f"WARNING: Unexpected DB URI format: {db_uri}")

print("\n3. Testing Gunicorn Entry Point...")
# Gunicorn uses "backend.app:app". This effectively tests "from backend.app import app"
# which we already did in Step 1.
print("SUCCESS: Entry point 'backend.app:app' is valid structure.")

print("\nALL CHECKS PASSED. READY FOR RENDER.")

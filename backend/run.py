# run.py - Updated version for better Railway deployment
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root directory to Python's module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create required directories for Railway deployment
def ensure_upload_directories():
    """Ensure upload directories exist for Railway deployment"""
    upload_dirs = [
        '/tmp/uploads',
        '/tmp/uploads/profiles',
        '/tmp/uploads/photos',
        '/tmp/uploads/videos'
    ]
    
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def initialize_database():
    """Initialize database tables if needed"""
    try:
        from flask_migrate import upgrade
        with app.app_context():
            # Try to upgrade database schema
            try:
                upgrade()
                print("Database migrations applied successfully")
            except Exception as e:
                print(f"Database migration warning: {e}")
                # If migrations fail, try to create all tables
                from app import db
                db.create_all()
                print("Database tables created")
    except Exception as e:
        print(f"Database initialization error: {e}")

# Import app after path setup
from app import create_app

# Create Flask app
app = create_app()

# Initialize required components for Railway
with app.app_context():
    ensure_upload_directories()
    initialize_database()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
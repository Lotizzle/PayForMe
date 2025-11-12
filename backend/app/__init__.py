import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, jsonify, request
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.utils.redis_client import get_redis_client
from flask_cors import CORS
from flask_uploads import configure_uploads, IMAGES, UploadSet
from config import Config
from flask_caching import Cache
from app.utils.tasks import make_celery
import os

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per day", "200 per hour"])
photos = UploadSet('photos', IMAGES)
videos = UploadSet('videos', ('mp4', 'avi', 'mov'))
cache = Cache()

# Create logger at module level
logger = logging.getLogger(__name__)

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_upload_directories(app):
    """Create upload directories for Railway deployment"""
    upload_dirs = [
        app.config.get('UPLOAD_FOLDERS', '/tmp/uploads'),
        app.config.get('UPLOADED_PHOTOS_DEST', '/tmp/uploads/photos'),
        app.config.get('UPLOADED_VIDEOS_DEST', '/tmp/uploads/videos'),
        os.path.join(app.root_path, 'static', 'uploads', 'profiles') if app.root_path else '/tmp/uploads/profiles'
    ]
    
    for directory in upload_dirs:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created upload directory: {directory}")
        except Exception as e:
            logger.warning(f"Could not create directory {directory}: {e}")

def create_app():
    # Configure logging first
    configure_logging()

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)

    # Create upload directories
    create_upload_directories(app)

    # Set upload folder configuration for Railway
    app.config['UPLOAD_FOLDER'] = app.config.get('UPLOADED_PHOTOS_DEST', '/tmp/uploads/profiles')
    app.config['UPLOADED_FILES_URL'] = '/uploads/'

    try:
        # Configure Flask-Uploads with error handling
        try:
            configure_uploads(app, (photos, videos))
        except Exception as e:
            logger.warning(f"Flask-Uploads configuration warning: {e}")

        # Initialize Redis client within app context
        try:
            with app.app_context():
                app.redis_client = get_redis_client()
        except Exception as e:
            logger.warning(f"Redis connection warning: {e}")
            app.redis_client = None

        # Initialize Flask extensions
        cache.init_app(app) 
        db.init_app(app)
        migrate.init_app(app, db)
        jwt.init_app(app)
        
        # Initialize rate limiter with error handling
        try:
            limiter.init_app(app)
        except Exception as e:
            logger.warning(f"Rate limiter initialization warning: {e}")
        
        # Configure CORS
        CORS(app, supports_credentials=True, resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:3000",
                    "https://your-frontend-domain.com",
                    os.environ.get('FRONTEND_URL', 'http://localhost:3000')
                ],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "expose_headers": ["Content-Type", "Authorization"],
                "max_age": 600
            }
        })

        # Register blueprints
        register_blueprints(app)

        # Error handlers
        @app.errorhandler(422)
        def handle_validation_error(e):
            return jsonify({
                "status": "error",
                "message": "Invalid request data",
                "errors": e.data['messages'] if hasattr(e, 'data') else None
            }), 422

        @app.errorhandler(500)
        def handle_internal_error(e):
            logger.error(f"Internal server error: {e}")
            return jsonify({
                "status": "error",
                "message": "Internal server error"
            }), 500

        # Health check endpoint for Railway
        @app.route('/health')
        def health_check():
            return jsonify({"status": "healthy", "message": "API is running"}), 200

        return app

    except Exception as e:
        logger.error(f"Failed to initialize app extensions: {e}")
        raise

def register_blueprints(app):
    """Register all application blueprints"""
    try:
        # Auth-related routes
        from app.routes.auth import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

        # Google auth routes
        from app.routes.google_auth import google_auth
        app.register_blueprint(google_auth, url_prefix='/api/v1/google_auth/')

        # User-related routes
        from app.routes.profile_routes import profile_bp
        app.register_blueprint(profile_bp, url_prefix='/api/v1/profile')

        # 2FA routes
        from app.routes.two_factor_auth import two_factor_auth_bp
        app.register_blueprint(two_factor_auth_bp, url_prefix='/api/v1/auth/2fa')

        # Admin routes
        from app.routes.role_permissions import role_permissions_bp
        app.register_blueprint(role_permissions_bp, url_prefix='/api/v1/role_permissions')

        # Project routes
        from app.routes.projects import projects_bp
        app.register_blueprint(projects_bp, url_prefix='/api/v1/projects')

        # Categories routes
        from app.routes.categories import categories_bp
        app.register_blueprint(categories_bp, url_prefix='/api/v1/categories')

        # Backers routes
        from app.routes.backer_routes import backer_bp
        app.register_blueprint(backer_bp, url_prefix='/api/v1/backers')

        # Notification routes
        from app.routes.notifications import notifications_bp
        app.register_blueprint(notifications_bp, url_prefix='/api/v1/notifications')

        # Reward routes
        from app.routes.reward_routes import reward_bp
        app.register_blueprint(reward_bp, url_prefix='/api/v1/rewards')

        # Payout routes
        from app.routes.payout_routes import payout_bp
        app.register_blueprint(payout_bp, url_prefix='/api/v1/payouts')

        # Bank account routes
        from app.routes.bank_account_routes import bank_account_bp
        app.register_blueprint(bank_account_bp, url_prefix='/api/v1/bank-accounts')

        logger.info("All blueprints registered successfully")

    except ImportError as e:
        logger.error(f"Blueprint import error: {e}")
        raise
    except Exception as e:
        logger.error(f"Blueprint registration error: {e}")
        raise
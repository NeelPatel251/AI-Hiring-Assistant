from flask import Flask
from app.config.settings import settings
from app.api.v1.endpoints.resume_endpoint import resume_bp
from app.core.logger import get_logger


def create_app() -> Flask:
    """Create and configure the Flask application"""
    logger = get_logger(__name__)
    logger.info("Initializing Flask application")
    
    try:
        app = Flask(__name__, template_folder='../templates', static_folder=None)
        logger.debug("Flask app instance created")
        
        # Configure the app
        app.config['DEBUG'] = settings.DEBUG
        app.config['UPLOAD_FOLDER'] = settings.UPLOAD_FOLDER
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        
        logger.info(f"Flask configuration - DEBUG: {settings.DEBUG}, UPLOAD_FOLDER: {settings.UPLOAD_FOLDER}")
        logger.info(f"Max file size: {app.config['MAX_CONTENT_LENGTH']} bytes (16MB)")
        
        # Register blueprints
        logger.info("Registering blueprints")
        app.register_blueprint(resume_bp)
        logger.info("Resume blueprint registered successfully")
        
        # Add request logging middleware
        @app.before_request
        def log_request_info():
            from flask import request
            logger.debug(f"Incoming request: {request.method} {request.path} from {request.remote_addr}")
        
        @app.after_request
        def log_response_info(response):
            from flask import request
            logger.debug(f"Response: {request.method} {request.path} - {response.status_code}")
            return response
        
        @app.teardown_appcontext
        def log_teardown(error):
            if error:
                logger.error(f"Application context teardown error: {error}")
        
        logger.info("Flask application initialized successfully")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create Flask application: {str(e)}")
        raise
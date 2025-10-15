from flask import Flask
from app.config.settings import settings
from app.api.v1.endpoints.resume_endpoint import resume_bp


def create_app() -> Flask:
    """Create and configure the Flask application"""
    app = Flask(__name__, template_folder='../templates', static_folder=None)
    
    # Configure the app
    app.config['DEBUG'] = settings.DEBUG
    app.config['UPLOAD_FOLDER'] = settings.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Register blueprints
    # Register the main resume blueprint directly for web interface
    app.register_blueprint(resume_bp)
    
    # You can also register API blueprints if needed:
    # from app.api.v1 import api_v1
    # app.register_blueprint(api_v1)
    
    return app
from flask import Blueprint
from .resume_endpoint import resume_bp

# Create main API blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Register all endpoint blueprints
api_v1.register_blueprint(resume_bp, url_prefix='/resume')

# Export the main blueprint and individual blueprints
__all__ = ['api_v1', 'resume_bp']
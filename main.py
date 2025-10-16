#!/usr/bin/env python3
"""
Resume Ranking System - Entry Point

This is the main entry point for the Flask application that provides
AI-powered resume ranking functionality.
"""

import sys
from app import create_app
from app.core.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

def main():
    """Main application entry point"""
    try:
        logger.info("Starting Resume Ranking System")
        logger.info(f"Python version: {sys.version}")
        
        # Create the Flask application using the application factory
        logger.info("Creating Flask application")
        app = create_app()
        
        if app is None:
            logger.error("Failed to create Flask application")
            sys.exit(1)
        
        logger.info("Flask application created successfully")
        logger.info("Starting development server on http://0.0.0.0:5000")
        
        # Run the application
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)

# Create the Flask application for deployment
app = create_app()

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Resume Ranking System - Entry Point

This is the main entry point for the Flask application that provides
AI-powered resume ranking functionality.
"""

from app import create_app

# Create the Flask application using the application factory
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
#!/usr/bin/env python3
"""
Simple test script to validate the refactored application structure
"""

def test_imports():
    """Test that all modules can be imported correctly"""
    try:
        print("Testing imports...")
        
        # Test configuration
        from app.config.settings import settings
        print("✓ Configuration module imported successfully")
        
        # Test models
        from app.models.schemas import ResumeRankingRequest, ResumeRankingResponse
        print("✓ Models imported successfully")
        
        # Test core utilities
        from app.core.file_utils import FileManager
        print("✓ Core utilities imported successfully")
        
        # Test services (will fail if dependencies not installed)
        from app.services.resume_service import ResumeJDMatcher
        from app.services.ranking_service import ResumeRankingService
        print("✓ Services imported successfully")
        
        # Test API endpoints
        from app.api.v1.endpoints.resume_endpoint import resume_bp
        print("✓ API endpoints imported successfully")
        
        # Test Flask app creation
        from app import create_app
        app = create_app()
        print("✓ Flask application created successfully")
        
        print("\n🎉 All imports successful! The refactored application structure is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports()
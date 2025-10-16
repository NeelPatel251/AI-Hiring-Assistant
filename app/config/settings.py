import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Claude Configuration
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY")
    
    # File Upload Configuration
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: set = {'.pdf', '.docx'}
    
    # Flask Configuration
    DEBUG: bool = True
    
    # Model Configuration
    SENTENCE_TRANSFORMER_MODEL: str = 'all-MiniLM-L6-v2'
    SENTENCE_TRANSFORMER_MODEL_ADVANCED: str = 'all-mpnet-base-v2'
    
    # Claude Model Configuration
    CLAUDE_MODEL: str = "claude-4-sonnet-20250514"
    
    # Similarity Thresholds
    SECTION_SIMILARITY_THRESHOLD: float = 0.7
    
    def __init__(self):
        # Create upload directory if it doesn't exist
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)

# Create a global settings instance
settings = Settings()
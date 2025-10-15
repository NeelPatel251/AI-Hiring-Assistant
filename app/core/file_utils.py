import os
from typing import List, Tuple
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from app.config.settings import settings


class FileManager:
    """Utility class for handling file operations"""
    
    @staticmethod
    def clear_directory(directory_path: str) -> None:
        """Clear all files from a directory"""
        if os.path.exists(directory_path):
            for file in os.listdir(directory_path):
                file_path = os.path.join(directory_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    
    @staticmethod
    def save_uploaded_files(files: List[FileStorage], upload_dir: str) -> List[str]:
        """Save uploaded files to the specified directory"""
        saved_files = []
        
        # Ensure upload directory exists
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in files:
            if file and file.filename:
                # Secure the filename
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_dir, filename)
                
                # Save the file
                file.save(filepath)
                saved_files.append(filepath)
        
        return saved_files
    
    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """Check if the file extension is allowed"""
        if not filename:
            return False
        
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in settings.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_uploaded_files(files: List[FileStorage]) -> Tuple[bool, str]:
        """Validate uploaded files"""
        if not files or len(files) == 0:
            return False, "No files uploaded"
        
        for file in files:
            if not file or not file.filename:
                return False, "Invalid file uploaded"
            
            if not FileManager.is_allowed_file(file.filename):
                return False, f"File type not allowed: {file.filename}. Only PDF files are supported."
        
        return True, "All files are valid"
    
    @staticmethod
    def get_upload_directory() -> str:
        """Get the upload directory path"""
        return settings.UPLOAD_FOLDER
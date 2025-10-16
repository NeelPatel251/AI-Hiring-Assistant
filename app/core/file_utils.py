import os
from typing import List, Tuple
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from app.config.settings import settings
from app.core.logger import get_logger, log_method_calls


class FileManager:
    """Utility class for handling file operations"""
    
    @staticmethod
    @log_method_calls()
    def clear_directory(directory_path: str) -> None:
        """Clear all files from a directory"""
        logger = get_logger(__name__)
        logger.info(f"Clearing directory: {directory_path}")
        
        try:
            if os.path.exists(directory_path):
                files = os.listdir(directory_path)
                logger.debug(f"Found {len(files)} items in directory")
                
                files_removed = 0
                for file in files:
                    file_path = os.path.join(directory_path, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        files_removed += 1
                        logger.debug(f"Removed file: {file}")
                
                logger.info(f"Successfully cleared directory - {files_removed} files removed")
            else:
                logger.warning(f"Directory does not exist: {directory_path}")
                
        except Exception as e:
            logger.error(f"Error clearing directory {directory_path}: {str(e)}")
            raise
    
    @staticmethod
    @log_method_calls()
    def save_uploaded_files(files: List[FileStorage], upload_dir: str) -> List[str]:
        """Save uploaded files to the specified directory"""
        logger = get_logger(__name__)
        logger.info(f"Saving {len(files)} uploaded files to directory: {upload_dir}")
        
        saved_files = []
        
        try:
            # Ensure upload directory exists
            os.makedirs(upload_dir, exist_ok=True)
            logger.debug(f"Ensured upload directory exists: {upload_dir}")
            
            for i, file in enumerate(files, 1):
                if file and file.filename:
                    # Secure the filename
                    original_filename = file.filename
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(upload_dir, filename)
                    
                    logger.debug(f"Saving file {i}/{len(files)}: {original_filename} -> {filename}")
                    
                    # Save the file
                    file.save(filepath)
                    saved_files.append(filepath)
                    
                    # Get file size for logging
                    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                    logger.debug(f"Successfully saved {filename} ({file_size} bytes)")
                else:
                    logger.warning(f"Skipping invalid file {i}/{len(files)}: {file.filename if file else 'None'}")
            
            logger.info(f"Successfully saved {len(saved_files)} out of {len(files)} files")
            return saved_files
            
        except Exception as e:
            logger.error(f"Error saving uploaded files: {str(e)}")
            raise
    
    @staticmethod
    @log_method_calls()
    def is_allowed_file(filename: str) -> bool:
        """Check if the file extension is allowed"""
        logger = get_logger(__name__)
        
        if not filename:
            logger.debug("File validation failed: No filename provided")
            return False
        
        file_ext = os.path.splitext(filename)[1].lower()
        is_allowed = file_ext in settings.ALLOWED_EXTENSIONS
        
        logger.debug(f"File extension validation for '{filename}': {file_ext} -> {'ALLOWED' if is_allowed else 'REJECTED'}")
        
        return is_allowed
    
    @staticmethod
    @log_method_calls()
    def validate_uploaded_files(files: List[FileStorage]) -> Tuple[bool, str]:
        """Validate uploaded files"""
        logger = get_logger(__name__)
        logger.info(f"Validating {len(files) if files else 0} uploaded files")
        
        if not files or len(files) == 0:
            logger.warning("File validation failed: No files uploaded")
            return False, "No files uploaded"
        
        for i, file in enumerate(files, 1):
            logger.debug(f"Validating file {i}/{len(files)}: {file.filename if file else 'None'}")
            
            if not file or not file.filename:
                logger.warning(f"File validation failed: Invalid file {i}")
                return False, "Invalid file uploaded"
            
            if not FileManager.is_allowed_file(file.filename):
                logger.warning(f"File validation failed: Unsupported file type for {file.filename}")
                return False, f"File type not allowed: {file.filename}. Only PDF files are supported."
        
        logger.info("All files passed validation")
        return True, "All files are valid"
    
    @staticmethod
    def get_upload_directory() -> str:
        """Get the upload directory path"""
        logger = get_logger(__name__)
        upload_dir = settings.UPLOAD_FOLDER
        logger.debug(f"Upload directory path: {upload_dir}")
        return upload_dir
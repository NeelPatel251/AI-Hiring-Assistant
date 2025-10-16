import logging
import os
import sys
from datetime import datetime
from functools import wraps
from typing import Any, Callable
from app.config.settings import settings


class LoggerConfig:
    """Centralized logging configuration for the resume ranking system"""
    
    _loggers = {}
    
    @classmethod
    def setup_logger(cls, name: str, level: str = "INFO") -> logging.Logger:
        """Setup and configure a logger with the given name"""
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Clear any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (if not in debug mode or explicitly enabled)
        if not settings.DEBUG or os.getenv('ENABLE_FILE_LOGGING', 'false').lower() == 'true':
            # Create logs directory if it doesn't exist
            log_dir = 'logs'
            os.makedirs(log_dir, exist_ok=True)
            
            # Create log file with current date
            log_file = os.path.join(log_dir, f'resume_ranking_{datetime.now().strftime("%Y%m%d")}.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        cls._loggers[name] = logger
        return logger


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""
    return LoggerConfig.setup_logger(name)


def log_execution_time(logger: logging.Logger = None):
    """Decorator to log function execution time"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = datetime.now()
            logger.info(f"Starting execution of {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                logger.info(f"Completed {func.__name__} in {execution_time:.2f} seconds")
                return result
            except Exception as e:
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                logger.error(f"Error in {func.__name__} after {execution_time:.2f} seconds: {str(e)}")
                raise
        
        return wrapper
    return decorator


def log_method_calls(logger: logging.Logger = None):
    """Decorator to log method calls with parameters (excluding sensitive data)"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            # Log method call (be careful with sensitive data)
            func_name = func.__name__
            class_name = args[0].__class__.__name__ if args and hasattr(args[0], '__class__') else ''
            full_name = f"{class_name}.{func_name}" if class_name else func_name
            
            # Filter out sensitive information
            safe_kwargs = {}
            for key, value in kwargs.items():
                if 'password' in key.lower() or 'key' in key.lower() or 'token' in key.lower():
                    safe_kwargs[key] = '***masked***'
                else:
                    safe_kwargs[key] = str(value)[:100]  # Truncate long values
            
            logger.debug(f"Calling {full_name} with kwargs: {safe_kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Successfully completed {full_name}")
                return result
            except Exception as e:
                logger.error(f"Error in {full_name}: {str(e)}")
                raise
        
        return wrapper
    return decorator


def log_api_request(logger: logging.Logger = None):
    """Decorator specifically for logging API requests"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal logger
            if logger is None:
                logger = get_logger('api')
            
            from flask import request
            
            # Log request details
            logger.info(f"API Request - {request.method} {request.endpoint} from {request.remote_addr}")
            logger.debug(f"Request headers: {dict(request.headers)}")
            
            if request.is_json and request.json:
                # Filter sensitive data from request body
                safe_data = {}
                for key, value in request.json.items():
                    if 'password' in key.lower() or 'key' in key.lower():
                        safe_data[key] = '***masked***'
                    else:
                        safe_data[key] = str(value)[:200]  # Truncate long values
                logger.debug(f"Request body: {safe_data}")
            
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                # Extract status code from response
                status_code = 200
                if hasattr(result, '__iter__') and len(result) > 1:
                    status_code = result[1] if isinstance(result[1], int) else 200
                
                logger.info(f"API Response - {request.method} {request.endpoint} - {status_code} - {execution_time:.2f}s")
                return result
            except Exception as e:
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                logger.error(f"API Error - {request.method} {request.endpoint} - {execution_time:.2f}s - Error: {str(e)}")
                raise
        
        return wrapper
    return decorator
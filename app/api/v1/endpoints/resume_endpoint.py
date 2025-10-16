from flask import Blueprint, request, render_template, jsonify
from typing import List
from werkzeug.datastructures import FileStorage
from app.services.resume_service import ResumeJDMatcher
from app.services.ranking_service import ResumeRankingService
from app.core.file_utils import FileManager
from app.models.schemas import ErrorResponse
from app.config.settings import settings
from app.core.logger import get_logger, log_api_request, log_execution_time

resume_bp = Blueprint('resume', __name__)
logger = get_logger(__name__)


@resume_bp.route('/health', methods=['GET'])
@log_api_request()
def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return jsonify({"status": "healthy", "service": "resume-ranking-api"}), 200


@resume_bp.route('/', methods=['GET', 'POST'])
@log_api_request()
def index():
    """Main endpoint for resume ranking with web interface"""
    ranked_resumes = []
    error_message = None
    job_description = ""
    processing = False
    analysis_mode = "multiple"
    threshold = 70
    
    if request.method == 'GET':
        logger.info("Serving main web interface (GET request)")
    
    if request.method == 'POST':
        logger.info("Processing resume ranking request via web interface")
        
        try:
            # Get form data
            job_description = request.form.get('job_desc', '').strip()
            analysis_mode = request.form.get('analysis_mode', 'multiple')
            threshold = float(request.form.get('threshold', 70))
            
            logger.info(f"Request parameters - Analysis mode: {analysis_mode}, Threshold: {threshold}%")
            logger.debug(f"Job description length: {len(job_description)} characters")
            
            if not job_description:
                logger.warning("Request rejected: Missing job description")
                error_message = "Job description is required"
                return render_template('index.html',
                                     ranked_resumes=ranked_resumes,
                                     error=error_message,
                                     job_description=job_description,
                                     analysis_mode=analysis_mode,
                                     threshold=threshold)
            
            # Get uploaded files
            resume_files: List[FileStorage] = request.files.getlist('resumes')
            logger.info(f"Received {len(resume_files)} uploaded files")
            
            # For single resume mode, ensure only one file is uploaded
            if analysis_mode == 'single' and len(resume_files) > 1:
                logger.warning(f"Single mode requested but {len(resume_files)} files uploaded")
                error_message = "Please upload only one resume file for single resume analysis"
                return render_template('index.html',
                                     ranked_resumes=ranked_resumes,
                                     error=error_message,
                                     job_description=job_description,
                                     analysis_mode=analysis_mode,
                                     threshold=threshold)
            
            # Validate files
            logger.debug("Validating uploaded files")
            is_valid, validation_message = FileManager.validate_uploaded_files(resume_files)
            if not is_valid:
                logger.warning(f"File validation failed: {validation_message}")
                error_message = validation_message
                return render_template('index.html',
                                     ranked_resumes=ranked_resumes,
                                     error=error_message,
                                     job_description=job_description,
                                     analysis_mode=analysis_mode,
                                     threshold=threshold)
            
            # Clear upload directory and save files
            logger.info("Saving uploaded files")
            upload_dir = FileManager.get_upload_directory()
            FileManager.clear_directory(upload_dir)
            saved_files = FileManager.save_uploaded_files(resume_files, upload_dir)
            logger.info(f"Successfully saved {len(saved_files)} files")
            
            if not saved_files:
                logger.error("No files were successfully uploaded")
                error_message = "No files were successfully uploaded"
                return render_template('index.html',
                                     ranked_resumes=ranked_resumes,
                                     error=error_message,
                                     job_description=job_description,
                                     analysis_mode=analysis_mode,
                                     threshold=threshold)
            
            # Process resumes
            processing = True
            logger.info("Starting resume processing")
            matcher = ResumeJDMatcher(job_description)
            results = matcher.process_resumes(upload_dir)
            
            if not results:
                logger.error("No resumes could be processed successfully")
                error_message = "No resumes could be processed"
                return render_template('index.html',
                                     ranked_resumes=ranked_resumes,
                                     error=error_message,
                                     job_description=job_description,
                                     analysis_mode=analysis_mode,
                                     threshold=threshold)
            
            # Get ranking data for template with hiring decisions
            logger.info("Generating ranking data with hiring decisions")
            ranked_resumes = ResumeRankingService.get_ranking_data_with_hiring_decision(
                results, threshold / 100.0, analysis_mode
            )
            
            # Get hiring summary for statistics
            hiring_summary = ResumeRankingService.get_hiring_summary(ranked_resumes)
            logger.info(f"Processing complete - {len(ranked_resumes)} resumes ranked")
            
            # Clean up uploaded files
            logger.debug("Cleaning up uploaded files")
            FileManager.clear_directory(upload_dir)
            
        except ValueError as e:
            logger.error(f"ValueError in web interface: {str(e)}")
            error_message = "Please enter a valid threshold percentage (0-100)"
            return render_template('index.html',
                                 ranked_resumes=ranked_resumes,
                                 error=error_message,
                                 job_description=job_description,
                                 analysis_mode=analysis_mode,
                                 threshold=threshold)
        except Exception as e:
            logger.error(f"Unexpected error in web interface: {str(e)}")
            error_message = f"An error occurred while processing resumes: {str(e)}"
            # Clean up in case of error
            try:
                FileManager.clear_directory(FileManager.get_upload_directory())
                logger.debug("Cleaned up files after error")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup files after error: {str(cleanup_error)}")
    
    return render_template('index.html',
                         ranked_resumes=ranked_resumes,
                         error=error_message,
                         job_description=job_description,
                         processing=processing,
                         analysis_mode=analysis_mode,
                         threshold=threshold,
                         hiring_summary=hiring_summary if 'hiring_summary' in locals() else None)


@resume_bp.route('/api/rank', methods=['POST'])
@log_api_request()
def rank_resumes_api():
    """API endpoint for resume ranking (JSON response)"""
    logger.info("Processing API resume ranking request")
    
    try:
        # Check if request has files
        if 'resumes' not in request.files:
            logger.warning("API request rejected: No files provided")
            return jsonify(ErrorResponse(
                error="No files provided",
                message="Please upload resume files",
                status_code=400
            ).dict()), 400
        
        # Get job description
        job_description = request.form.get('job_desc', '').strip()
        if not job_description:
            logger.warning("API request rejected: Missing job description")
            return jsonify(ErrorResponse(
                error="Missing job description",
                message="Job description is required",
                status_code=400
            ).dict()), 400
        
        logger.debug(f"API request - Job description length: {len(job_description)} characters")
        
        # Get uploaded files
        resume_files: List[FileStorage] = request.files.getlist('resumes')
        logger.info(f"API request received {len(resume_files)} files")
        
        # Validate files
        logger.debug("Validating uploaded files for API request")
        is_valid, validation_message = FileManager.validate_uploaded_files(resume_files)
        if not is_valid:
            logger.warning(f"API file validation failed: {validation_message}")
            return jsonify(ErrorResponse(
                error="Invalid files",
                message=validation_message,
                status_code=400
            ).dict()), 400
        
        # Clear upload directory and save files
        logger.info("Saving files for API processing")
        upload_dir = FileManager.get_upload_directory()
        FileManager.clear_directory(upload_dir)
        saved_files = FileManager.save_uploaded_files(resume_files, upload_dir)
        logger.info(f"Successfully saved {len(saved_files)} files for API processing")
        
        if not saved_files:
            logger.error("API processing failed: No files were successfully uploaded")
            return jsonify(ErrorResponse(
                error="File upload failed",
                message="No files were successfully uploaded",
                status_code=400
            ).dict()), 400
        
        # Process resumes
        logger.info("Starting resume processing for API request")
        matcher = ResumeJDMatcher(job_description)
        results = matcher.process_resumes(upload_dir)
        
        if not results:
            logger.error("API processing failed: No resumes could be processed")
            return jsonify(ErrorResponse(
                error="Processing failed",
                message="No resumes could be processed",
                status_code=400
            ).dict()), 400
        
        # Get ranking response
        logger.info("Generating ranking response for API")
        ranking_response = ResumeRankingService.rank_resumes(results)
        
        # Clean up uploaded files
        logger.debug("Cleaning up files after API processing")
        FileManager.clear_directory(upload_dir)
        
        logger.info(f"API request completed successfully - {len(results)} resumes processed")
        return jsonify(ranking_response.dict()), 200
        
    except Exception as e:
        logger.error(f"API request failed with error: {str(e)}")
        # Clean up in case of error
        try:
            FileManager.clear_directory(FileManager.get_upload_directory())
            logger.debug("Cleaned up files after API error")
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup files after API error: {str(cleanup_error)}")
        
        return jsonify(ErrorResponse(
            error="Internal server error",
            message=str(e),
            status_code=500
        ).dict()), 500


@resume_bp.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    logger.warning(f"File too large error: {str(e)}")
    return jsonify(ErrorResponse(
        error="File too large",
        message="The uploaded file is too large",
        status_code=413
    ).dict()), 413


@resume_bp.errorhandler(400)
def bad_request(e):
    """Handle bad request error"""
    logger.warning(f"Bad request error: {str(e)}")
    return jsonify(ErrorResponse(
        error="Bad request",
        message="Invalid request format",
        status_code=400
    ).dict()), 400
from flask import Blueprint, request, render_template, jsonify
from typing import List
from werkzeug.datastructures import FileStorage
from app.services.resume_service import ResumeJDMatcher
from app.services.ranking_service import ResumeRankingService
from app.core.file_utils import FileManager
from app.models.schemas import ErrorResponse
from app.config.settings import settings

resume_bp = Blueprint('resume', __name__)


@resume_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "resume-ranking-api"}), 200


@resume_bp.route('/', methods=['GET', 'POST'])
def index():
    """Main endpoint for resume ranking with web interface"""
    ranked_resumes = []
    error_message = None
    job_description = ""
    processing = False
    analysis_mode = "multiple"
    threshold = 70
    
    if request.method == 'POST':
        try:
            # Get form data
            job_description = request.form.get('job_desc', '').strip()
            analysis_mode = request.form.get('analysis_mode', 'multiple')
            threshold = float(request.form.get('threshold', 70))
            
            if not job_description:
                error_message = "Job description is required"
                return render_template('index.html',
                                     ranked_resumes=ranked_resumes,
                                     error=error_message,
                                     job_description=job_description,
                                     analysis_mode=analysis_mode,
                                     threshold=threshold)
            
            # Get uploaded files
            resume_files: List[FileStorage] = request.files.getlist('resumes')
            
            # For single resume mode, ensure only one file is uploaded
            if analysis_mode == 'single' and len(resume_files) > 1:
                error_message = "Please upload only one resume file for single resume analysis"
                return render_template('index.html',
                                     ranked_resumes=ranked_resumes,
                                     error=error_message,
                                     job_description=job_description,
                                     analysis_mode=analysis_mode,
                                     threshold=threshold)
            
            # Validate files
            is_valid, validation_message = FileManager.validate_uploaded_files(resume_files)
            if not is_valid:
                error_message = validation_message
                return render_template('index.html',
                                     ranked_resumes=ranked_resumes,
                                     error=error_message,
                                     job_description=job_description,
                                     analysis_mode=analysis_mode,
                                     threshold=threshold)
            
            # Clear upload directory and save files
            upload_dir = FileManager.get_upload_directory()
            FileManager.clear_directory(upload_dir)
            saved_files = FileManager.save_uploaded_files(resume_files, upload_dir)
            
            if not saved_files:
                error_message = "No files were successfully uploaded"
                return render_template('index.html',
                                     ranked_resumes=ranked_resumes,
                                     error=error_message,
                                     job_description=job_description,
                                     analysis_mode=analysis_mode,
                                     threshold=threshold)
            
            # Process resumes
            processing = True
            matcher = ResumeJDMatcher(job_description)
            results = matcher.process_resumes(upload_dir)
            
            if not results:
                error_message = "No resumes could be processed"
                return render_template('index.html',
                                     ranked_resumes=ranked_resumes,
                                     error=error_message,
                                     job_description=job_description,
                                     analysis_mode=analysis_mode,
                                     threshold=threshold)
            
            # Get ranking data for template with hiring decisions
            ranked_resumes = ResumeRankingService.get_ranking_data_with_hiring_decision(
                results, threshold / 100.0, analysis_mode
            )
            
            # Get hiring summary for statistics
            hiring_summary = ResumeRankingService.get_hiring_summary(ranked_resumes)
            
            # Clean up uploaded files
            FileManager.clear_directory(upload_dir)
            
        except ValueError:
            error_message = "Please enter a valid threshold percentage (0-100)"
            return render_template('index.html',
                                 ranked_resumes=ranked_resumes,
                                 error=error_message,
                                 job_description=job_description,
                                 analysis_mode=analysis_mode,
                                 threshold=threshold)
        except Exception as e:
            error_message = f"An error occurred while processing resumes: {str(e)}"
            # Clean up in case of error
            try:
                FileManager.clear_directory(FileManager.get_upload_directory())
            except:
                pass
    
    return render_template('index.html',
                         ranked_resumes=ranked_resumes,
                         error=error_message,
                         job_description=job_description,
                         processing=processing,
                         analysis_mode=analysis_mode,
                         threshold=threshold,
                         hiring_summary=hiring_summary if 'hiring_summary' in locals() else None)


@resume_bp.route('/api/rank', methods=['POST'])
def rank_resumes_api():
    """API endpoint for resume ranking (JSON response)"""
    try:
        # Check if request has files
        if 'resumes' not in request.files:
            return jsonify(ErrorResponse(
                error="No files provided",
                message="Please upload resume files",
                status_code=400
            ).dict()), 400
        
        # Get job description
        job_description = request.form.get('job_desc', '').strip()
        if not job_description:
            return jsonify(ErrorResponse(
                error="Missing job description",
                message="Job description is required",
                status_code=400
            ).dict()), 400
        
        # Get uploaded files
        resume_files: List[FileStorage] = request.files.getlist('resumes')
        
        # Validate files
        is_valid, validation_message = FileManager.validate_uploaded_files(resume_files)
        if not is_valid:
            return jsonify(ErrorResponse(
                error="Invalid files",
                message=validation_message,
                status_code=400
            ).dict()), 400
        
        # Clear upload directory and save files
        upload_dir = FileManager.get_upload_directory()
        FileManager.clear_directory(upload_dir)
        saved_files = FileManager.save_uploaded_files(resume_files, upload_dir)
        
        if not saved_files:
            return jsonify(ErrorResponse(
                error="File upload failed",
                message="No files were successfully uploaded",
                status_code=400
            ).dict()), 400
        
        # Process resumes
        matcher = ResumeJDMatcher(job_description)
        results = matcher.process_resumes(upload_dir)
        
        if not results:
            return jsonify(ErrorResponse(
                error="Processing failed",
                message="No resumes could be processed",
                status_code=400
            ).dict()), 400
        
        # Get ranking response
        ranking_response = ResumeRankingService.rank_resumes(results)
        
        # Clean up uploaded files
        FileManager.clear_directory(upload_dir)
        
        return jsonify(ranking_response.dict()), 200
        
    except Exception as e:
        # Clean up in case of error
        try:
            FileManager.clear_directory(FileManager.get_upload_directory())
        except:
            pass
        
        return jsonify(ErrorResponse(
            error="Internal server error",
            message=str(e),
            status_code=500
        ).dict()), 500


@resume_bp.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify(ErrorResponse(
        error="File too large",
        message="The uploaded file is too large",
        status_code=413
    ).dict()), 413


@resume_bp.errorhandler(400)
def bad_request(e):
    """Handle bad request error"""
    return jsonify(ErrorResponse(
        error="Bad request",
        message="Invalid request format",
        status_code=400
    ).dict()), 400
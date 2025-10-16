from typing import List
from app.models.schemas import ResumeProcessingResult, RankedResume, ResumeRankingResponse
from app.core.logger import get_logger, log_method_calls, log_execution_time


class ResumeRankingService:
    """Service for ranking resumes based on similarity scores"""
    
    @staticmethod
    @log_execution_time()
    @log_method_calls()
    def rank_resumes(results: List[ResumeProcessingResult]) -> ResumeRankingResponse:
        """Rank resumes by their combined scores"""
        logger = get_logger(__name__)
        logger.info(f"Starting ranking of {len(results)} resumes")
        
        try:
            # Sort results by combined score in descending order
            sorted_results = sorted(results, key=lambda x: x.combined_score, reverse=True)
            logger.debug("Resumes sorted by combined score")
            
            # Log score distribution
            if sorted_results:
                scores = [r.combined_score for r in sorted_results]
                logger.info(f"Score range: {min(scores):.4f} to {max(scores):.4f}")
            
            # Create ranked resume objects
            ranked_resumes = []
            for rank, result in enumerate(sorted_results, 1):
                logger.debug(f"Ranking resume '{result.filename}' at position {rank} with score {result.combined_score:.4f}")
                
                ranked_resume = RankedResume(
                    resume_name=result.filename,
                    combined_score=result.combined_score,
                    rank=rank
                )
                ranked_resumes.append(ranked_resume)
            
            response = ResumeRankingResponse(
                ranked_resumes=ranked_resumes,
                total_resumes=len(ranked_resumes)
            )
            
            logger.info(f"Successfully ranked {len(ranked_resumes)} resumes")
            return response
            
        except Exception as e:
            logger.error(f"Error ranking resumes: {str(e)}")
            raise
    
    @staticmethod
    @log_method_calls()
    def get_ranking_data_for_template(results: List[ResumeProcessingResult]) -> List[tuple]:
        """Get ranking data in the format expected by the Flask template"""
        logger = get_logger(__name__)
        logger.info(f"Generating template ranking data for {len(results)} resumes")
        
        try:
            # Sort results by combined score in descending order
            sorted_results = sorted(results, key=lambda x: x.combined_score, reverse=True)
            
            # Return as list of tuples (filename, combined_score)
            template_data = [(result.filename, result.combined_score) for result in sorted_results]
            logger.debug(f"Generated template data with {len(template_data)} items")
            
            return template_data
            
        except Exception as e:
            logger.error(f"Error generating template ranking data: {str(e)}")
            raise
    
    @staticmethod
    @log_execution_time()
    @log_method_calls()
    def get_ranking_data_with_hiring_decision(results: List[ResumeProcessingResult],
                                            threshold: float,
                                            mode: str) -> List[dict]:
        """Get ranking data with hiring decisions based on threshold and mode"""
        logger = get_logger(__name__)
        logger.info(f"Generating ranking data with hiring decisions - Threshold: {threshold:.2f}, Mode: {mode}")
        
        try:
            # Sort results by combined score in descending order
            sorted_results = sorted(results, key=lambda x: x.combined_score, reverse=True)
            logger.debug(f"Sorted {len(sorted_results)} results by combined score")
            
            # Create enhanced result data with hiring decisions
            enhanced_results = []
            hired_count = 0
            
            for rank, result in enumerate(sorted_results, 1):
                # Determine if candidate should be hired
                should_hire = result.combined_score >= threshold
                if should_hire:
                    hired_count += 1
                
                logger.debug(f"Resume '{result.filename}' - Rank: {rank}, Score: {result.combined_score:.4f}, Decision: {'HIRE' if should_hire else 'NOT HIRE'}")
                
                enhanced_result = {
                    'filename': result.filename,
                    'combined_score': result.combined_score,
                    'rank': rank,
                    'should_hire': should_hire,
                    'hire_status': 'HIRE' if should_hire else 'NOT HIRE',
                    'hire_class': 'success' if should_hire else 'danger',
                    'section_scores': result.section_scores,
                    'average_score': result.average_score,
                    'full_text_similarity': result.full_text_similarity,
                    'mode': mode
                }
                enhanced_results.append(enhanced_result)
            
            hire_percentage = (hired_count / len(results) * 100) if results else 0
            logger.info(f"Hiring decisions complete - {hired_count}/{len(results)} candidates to hire ({hire_percentage:.1f}%)")
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error generating ranking data with hiring decisions: {str(e)}")
            raise
    
    @staticmethod
    @log_method_calls()
    def get_hiring_summary(results: List[dict]) -> dict:
        """Get hiring summary statistics"""
        logger = get_logger(__name__)
        logger.info(f"Generating hiring summary for {len(results)} candidates")
        
        try:
            total_candidates = len(results)
            hired_candidates = len([r for r in results if r['should_hire']])
            not_hired_candidates = total_candidates - hired_candidates
            hire_percentage = (hired_candidates / total_candidates * 100) if total_candidates > 0 else 0
            
            summary = {
                'total_candidates': total_candidates,
                'hired_candidates': hired_candidates,
                'not_hired_candidates': not_hired_candidates,
                'hire_percentage': hire_percentage
            }
            
            logger.info(f"Hiring summary - Total: {total_candidates}, Hired: {hired_candidates}, Not Hired: {not_hired_candidates}, Percentage: {hire_percentage:.1f}%")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating hiring summary: {str(e)}")
            raise
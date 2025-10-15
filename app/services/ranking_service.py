from typing import List
from app.models.schemas import ResumeProcessingResult, RankedResume, ResumeRankingResponse


class ResumeRankingService:
    """Service for ranking resumes based on similarity scores"""
    
    @staticmethod
    def rank_resumes(results: List[ResumeProcessingResult]) -> ResumeRankingResponse:
        """Rank resumes by their combined scores"""
        # Sort results by combined score in descending order
        sorted_results = sorted(results, key=lambda x: x.combined_score, reverse=True)
        
        # Create ranked resume objects
        ranked_resumes = []
        for rank, result in enumerate(sorted_results, 1):
            ranked_resume = RankedResume(
                resume_name=result.filename,
                combined_score=result.combined_score,
                rank=rank
            )
            ranked_resumes.append(ranked_resume)
        
        return ResumeRankingResponse(
            ranked_resumes=ranked_resumes,
            total_resumes=len(ranked_resumes)
        )
    
    @staticmethod
    def get_ranking_data_for_template(results: List[ResumeProcessingResult]) -> List[tuple]:
        """Get ranking data in the format expected by the Flask template"""
        # Sort results by combined score in descending order
        sorted_results = sorted(results, key=lambda x: x.combined_score, reverse=True)
        
        # Return as list of tuples (filename, combined_score)
        return [(result.filename, result.combined_score) for result in sorted_results]
    
    @staticmethod
    def get_ranking_data_with_hiring_decision(results: List[ResumeProcessingResult],
                                            threshold: float,
                                            mode: str) -> List[dict]:
        """Get ranking data with hiring decisions based on threshold and mode"""
        # Sort results by combined score in descending order
        sorted_results = sorted(results, key=lambda x: x.combined_score, reverse=True)
        
        # Create enhanced result data with hiring decisions
        enhanced_results = []
        for rank, result in enumerate(sorted_results, 1):
            # Determine if candidate should be hired
            should_hire = result.combined_score >= threshold
            
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
        
        return enhanced_results
    
    @staticmethod
    def get_hiring_summary(results: List[dict]) -> dict:
        """Get hiring summary statistics"""
        total_candidates = len(results)
        hired_candidates = len([r for r in results if r['should_hire']])
        not_hired_candidates = total_candidates - hired_candidates
        
        return {
            'total_candidates': total_candidates,
            'hired_candidates': hired_candidates,
            'not_hired_candidates': not_hired_candidates,
            'hire_percentage': (hired_candidates / total_candidates * 100) if total_candidates > 0 else 0
        }
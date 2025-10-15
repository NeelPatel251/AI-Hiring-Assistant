from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from werkzeug.datastructures import FileStorage

class ResumeRankingRequest(BaseModel):
    """Request model for resume ranking"""
    job_description: str = Field(..., description="Job description text to match against resumes")
    
    class Config:
        # Allow arbitrary types for FileStorage
        arbitrary_types_allowed = True

class SectionScores(BaseModel):
    """Section-wise similarity scores for a resume"""
    Experience: Optional[float] = None
    Education: Optional[float] = None
    Projects: Optional[float] = None
    Skills: Optional[float] = None
    Certifications: Optional[float] = None
    Achievements: Optional[float] = None

class ResumeAnalysisResult(BaseModel):
    """Analysis result for a single resume"""
    section_scores: Dict[str, float] = Field(..., alias="Section-wise Scores")
    average_score: float = Field(..., alias="Average Score")
    full_text_similarity: float = Field(..., alias="Full Text Similarity")

class RankedResume(BaseModel):
    """Individual ranked resume item"""
    resume_name: str
    combined_score: float
    rank: int

class ResumeRankingResponse(BaseModel):
    """Response model for resume ranking"""
    ranked_resumes: List[RankedResume]
    total_resumes: int
    
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    status_code: int = 400

class ResumeProcessingResult(BaseModel):
    """Internal model for resume processing results"""
    filename: str
    section_scores: Dict[str, float]
    average_score: float
    full_text_similarity: float
    combined_score: float
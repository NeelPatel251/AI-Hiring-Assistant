import fitz
import torch
import re
import os
import time
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import anthropic
from app.config.settings import settings
from app.models.schemas import ResumeProcessingResult
from app.core.logger import get_logger, log_execution_time, log_method_calls


class ResumeJDMatcher:
    """Main service for matching resumes against job descriptions"""
    
    def __init__(self, job_description: str):
        self.logger = get_logger(__name__)
        self.logger.info("Initializing ResumeJDMatcher")
        
        self.job_description = job_description
        self.logger.info(f"Job description length: {len(job_description)} characters")
        
        try:
            self.logger.info(f"Loading sentence transformer models: {settings.SENTENCE_TRANSFORMER_MODEL} and {settings.SENTENCE_TRANSFORMER_MODEL_ADVANCED}")
            self.model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
            self.model1 = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL_ADVANCED)
            self.logger.info("Successfully loaded sentence transformer models")
            
            self.logger.info("Initializing Claude API client")
            self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
            self.logger.info("Successfully initialized Claude API client")
        except Exception as e:
            self.logger.error(f"Error initializing ResumeJDMatcher: {str(e)}")
            raise
        
    @log_execution_time()
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        self.logger.info(f"Extracting text from PDF: {os.path.basename(pdf_path)}")
        
        try:
            doc = fitz.open(pdf_path)
            text = ""
            page_count = doc.page_count
            self.logger.debug(f"PDF has {page_count} pages")
            
            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text("text")
                text += page_text + "\n"
                self.logger.debug(f"Extracted text from page {page_num}: {len(page_text)} characters")
            
            doc.close()
            extracted_text = text.strip()
            self.logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
            return extracted_text
            
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            raise

    @log_execution_time()
    def extract_sections(self, resume_text: str) -> Dict[str, str]:
        """Extract and categorize sections from resume text"""
        self.logger.info("Starting section extraction from resume text")
        
        try:
            section_groups = {
                "Experience": ["experience", "work experience", "employment history", "internships", "professional experience"],
                "Education": ["education", "academic qualifications", "degrees", "coursework"],
                "Projects": ["projects", "academic projects", "personal projects"],
                "Skills": ["skills", "technical skills", "soft skills", "programming languages", "Technologies"],
                "Certifications": ["certifications", "licenses", "accreditations"],
                "Achievements": ["awards", "achievements", "honors", "research publications"],
            }

            keyword_to_group = {keyword: group for group, keywords in section_groups.items() for keyword in keywords}
            section_keywords = list(keyword_to_group.keys())
            self.logger.debug(f"Using {len(section_keywords)} section keywords for matching")

            self.logger.debug("Encoding section keywords")
            keyword_embeddings = self.model.encode(section_keywords, convert_to_tensor=True)
            
            lines = resume_text.split("\n")
            self.logger.debug(f"Processing {len(lines)} lines from resume")
            line_embeddings = self.model.encode(lines, convert_to_tensor=True)

            similarities = util.cos_sim(line_embeddings, keyword_embeddings)
            section_positions = []
            matched_sections = {}

            for i, line in enumerate(lines):
                max_sim, max_idx = torch.max(similarities[i], dim=0)
                stripped_line = line.strip()
                if max_sim > settings.SECTION_SIMILARITY_THRESHOLD and not re.match(r"^[-•]", stripped_line):
                    matched_group = keyword_to_group[section_keywords[max_idx]]
                    matched_sections[stripped_line] = matched_group
                    section_positions.append((i, matched_group))
                    self.logger.debug(f"Matched section: {matched_group} (similarity: {max_sim:.3f})")

            sections = {}
            for i in range(len(section_positions)):
                section_name = section_positions[i][1]
                start_idx = section_positions[i][0] + 1
                end_idx = section_positions[i + 1][0] if i + 1 < len(section_positions) else len(lines)
                section_content = "\n".join(lines[start_idx:end_idx]).strip()

                if section_name not in sections:
                    sections[section_name] = [section_content]
                else:
                    sections[section_name].append(section_content)

            result_sections = {section: "\n\n".join(content) for section, content in sections.items()}
            self.logger.info(f"Successfully extracted {len(result_sections)} sections: {list(result_sections.keys())}")
            
            return result_sections
            
        except Exception as e:
            self.logger.error(f"Error extracting sections: {str(e)}")
            raise

    @log_execution_time()
    def summarize_sections(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Summarize resume sections using Claude"""
        self.logger.info(f"Starting summarization of {len(sections)} sections using Claude")
        
        summarized_sections = {}
        successful_summaries = 0
        failed_summaries = 0
        
        for section_name, text in sections.items():
            section_start_time = time.time()
            
            if text.strip():
                try:
                    self.logger.debug(f"Summarizing section '{section_name}' ({len(text)} characters)")
                    
                    response = self.client.messages.create(
                        model=settings.CLAUDE_MODEL,
                        max_tokens=1000,
                        messages=[
                            {
                                "role": "user",
                                "content": f"You are an AI that summarizes Resume section content. Summarize the following section:\n\n{section_name}: {text}"
                            }
                        ]
                    )
                    
                    summary = response.content[0].text
                    summarized_sections[section_name] = summary
                    successful_summaries += 1
                    
                    section_time = time.time() - section_start_time
                    self.logger.info(f"Successfully summarized '{section_name}' in {section_time:.2f}s (original: {len(text)}, summary: {len(summary)} characters)")
                    
                except Exception as e:
                    section_time = time.time() - section_start_time
                    self.logger.error(f"Error summarizing section '{section_name}' after {section_time:.2f}s: {str(e)}")
                    # If Claude call fails, use original text
                    summarized_sections[section_name] = text
                    failed_summaries += 1
                    self.logger.warning(f"Using original text for section '{section_name}' due to summarization failure")
            else:
                summarized_sections[section_name] = "No content available."
                self.logger.debug(f"Section '{section_name}' has no content")
        
        self.logger.info(f"Summarization complete. Success: {successful_summaries}, Failed: {failed_summaries}")
        return summarized_sections

    @log_execution_time()
    def calculate_similarity(self, resume_text: str) -> Tuple[Dict[str, float], float, float]:
        """Calculate similarity scores between resume and job description"""
        self.logger.info("Starting similarity calculation")
        
        try:
            sections = self.extract_sections(resume_text)
            summarized_sections = self.summarize_sections(sections)
            scores = {}
            total_score = 0
            
            self.logger.debug("Encoding job description for similarity comparison")
            jd_embed = self.model1.encode(self.job_description).reshape(1, -1)
            
            for section, content in summarized_sections.items():
                self.logger.debug(f"Calculating similarity for section: {section}")
                embedding = self.model1.encode(content).reshape(1, -1)
                similarity = cosine_similarity(embedding, jd_embed)[0][0]
                scores[section] = similarity
                total_score += similarity
                self.logger.debug(f"Section '{section}' similarity: {similarity:.4f}")
            
            avg_score = total_score / len(scores) if scores else 0
            
            self.logger.debug("Calculating full text similarity")
            full_text_embedding = self.model1.encode(resume_text).reshape(1, -1)
            full_text_similarity = cosine_similarity(full_text_embedding, jd_embed)[0][0]
            
            self.logger.info(f"Similarity calculation complete - Average: {avg_score:.4f}, Full text: {full_text_similarity:.4f}")
            return scores, avg_score, full_text_similarity
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {str(e)}")
            raise

    @log_execution_time()
    def process_resume(self, pdf_path: str) -> ResumeProcessingResult:
        """Process a single resume file"""
        filename = os.path.basename(pdf_path)
        self.logger.info(f"Processing resume: {filename}")
        
        try:
            full_text = self.extract_text_from_pdf(pdf_path)
            section_scores, avg_score, full_text_score = self.calculate_similarity(full_text)
            
            # Calculate combined score
            combined_score = (avg_score + full_text_score) / 2
            
            result = ResumeProcessingResult(
                filename=filename,
                section_scores=section_scores,
                average_score=avg_score,
                full_text_similarity=full_text_score,
                combined_score=combined_score
            )
            
            self.logger.info(f"Successfully processed {filename} - Combined score: {combined_score:.4f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing resume {filename}: {str(e)}")
            raise

    @log_execution_time()
    def process_resumes(self, resume_dir: str) -> List[ResumeProcessingResult]:
        """Process all resumes in a directory"""
        self.logger.info(f"Starting batch processing of resumes in directory: {resume_dir}")
        
        try:
            pdf_files = [f for f in os.listdir(resume_dir) if f.endswith(".pdf")]
            self.logger.info(f"Found {len(pdf_files)} PDF files to process")
            
            results = []
            successful_count = 0
            failed_count = 0
            
            for filename in pdf_files:
                pdf_path = os.path.join(resume_dir, filename)
                try:
                    result = self.process_resume(pdf_path)
                    results.append(result)
                    successful_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to process {filename}: {str(e)}")
                    failed_count += 1
                    continue
            
            self.logger.info(f"Batch processing complete - Successful: {successful_count}, Failed: {failed_count}")
            
            if results:
                # Log summary statistics
                scores = [r.combined_score for r in results]
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                min_score = min(scores)
                self.logger.info(f"Score statistics - Average: {avg_score:.4f}, Max: {max_score:.4f}, Min: {min_score:.4f}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during batch processing: {str(e)}")
            raise
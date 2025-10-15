import fitz
import torch
import re
import os
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import openai
from app.config.settings import settings
from app.models.schemas import ResumeProcessingResult


class ResumeJDMatcher:
    """Main service for matching resumes against job descriptions"""
    
    def __init__(self, job_description: str):
        self.job_description = job_description
        self.model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
        self.model1 = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL_ADVANCED) 
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        return text.strip()

    def extract_sections(self, resume_text: str) -> Dict[str, str]:
        """Extract and categorize sections from resume text"""
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

        keyword_embeddings = self.model.encode(section_keywords, convert_to_tensor=True)
        lines = resume_text.split("\n")
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

        return {section: "\n\n".join(content) for section, content in sections.items()}

    def summarize_sections(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Summarize resume sections using OpenAI"""
        summarized_sections = {}
        for section_name, text in sections.items():
            if text.strip():
                try:
                    response = self.client.chat.completions.create(
                        model=settings.OPENAI_MODEL,
                        messages=[
                            {"role": "system", "content": "You are an AI that summarizes Resume section content."},
                            {"role": "user", "content": f"Summarize the following section:\n\n{section_name}: {text}"}
                        ]
                    )
                    summarized_sections[section_name] = response.choices[0].message.content
                except Exception as e:
                    # If OpenAI call fails, use original text
                    summarized_sections[section_name] = text
            else:
                summarized_sections[section_name] = "No content available."
        return summarized_sections

    def calculate_similarity(self, resume_text: str) -> Tuple[Dict[str, float], float, float]:
        """Calculate similarity scores between resume and job description"""
        sections = self.extract_sections(resume_text)
        summarized_sections = self.summarize_sections(sections)
        scores = {}
        total_score = 0
        
        for section, content in summarized_sections.items():
            embedding = self.model1.encode(content).reshape(1, -1)
            jd_embed = self.model1.encode(self.job_description).reshape(1, -1)
            similarity = cosine_similarity(embedding, jd_embed)[0][0]
            scores[section] = similarity
            total_score += similarity
        
        avg_score = total_score / len(scores) if scores else 0
        
        full_text_embedding = self.model1.encode(resume_text).reshape(1, -1)
        full_text_similarity = cosine_similarity(full_text_embedding, jd_embed)[0][0]
        
        return scores, avg_score, full_text_similarity

    def process_resume(self, pdf_path: str) -> ResumeProcessingResult:
        """Process a single resume file"""
        filename = os.path.basename(pdf_path)
        full_text = self.extract_text_from_pdf(pdf_path)
        section_scores, avg_score, full_text_score = self.calculate_similarity(full_text)
        
        # Calculate combined score
        combined_score = (avg_score + full_text_score) / 2
        
        return ResumeProcessingResult(
            filename=filename,
            section_scores=section_scores,
            average_score=avg_score,
            full_text_similarity=full_text_score,
            combined_score=combined_score
        )

    def process_resumes(self, resume_dir: str) -> List[ResumeProcessingResult]:
        """Process all resumes in a directory"""
        results = []
        for filename in os.listdir(resume_dir):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(resume_dir, filename)
                try:
                    result = self.process_resume(pdf_path)
                    results.append(result)
                except Exception as e:
                    # Log error and continue with other resumes
                    print(f"Error processing {filename}: {str(e)}")
                    continue
        return results
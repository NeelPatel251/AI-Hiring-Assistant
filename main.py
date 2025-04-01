import fitz
import torch
import re
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import openai
import os

class ResumeJDMatcher:
    def __init__(self, resume_dir, job_description, api_key):
        self.resume_dir = resume_dir
        self.job_description = job_description
        self.api_key = api_key
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.model1 = SentenceTransformer('all-mpnet-base-v2') 
        self.client = openai.OpenAI(api_key=self.api_key)
        
    def extract_text_from_pdf(self, pdf_path):
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        return text.strip()

    def extract_sections(self, resume_text):
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
            if max_sim > 0.7 and not re.match(r"^[-•]", stripped_line):
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

    def summarize_sections(self, sections):
        summarized_sections = {}
        for section_name, text in sections.items():
            if text.strip():
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an AI that summarizes Resume section content."},
                        {"role": "user", "content": f"Summarize the following section:\n\n{section_name}: {text}"}
                    ]
                )
                summarized_sections[section_name] = response.choices[0].message.content
            else:
                summarized_sections[section_name] = "No content available."
        return summarized_sections

    def calculate_similarity(self, resume_text):
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

    def process_resumes(self):
        results = {}
        for filename in os.listdir(self.resume_dir):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(self.resume_dir, filename)
                full_text = self.extract_text_from_pdf(pdf_path)
                section_scores, avg_score, full_text_score = self.calculate_similarity(full_text)
                results[filename] = {
                    "Section-wise Scores": section_scores,
                    "Average Score": avg_score,
                    "Full Text Similarity": full_text_score
                }
        return results

resume_directory = "uploads"
jd = "jd.txt"
with open(jd, "r") as file:
    job_description = file.read() 


api_key = "REDACTED_OPENAI_KEY"
matcher = ResumeJDMatcher(resume_directory, job_description, api_key)
results = matcher.process_resumes()

# for resume, data in results.items():
#     print(f"\nResume: {resume}")
#     for section, score in data["Section-wise Scores"].items():
#         print(f"{section}: {score}")
#     print(f"Average Cosine Similarity: {data['Average Score']}")
#     print(f"Full Text Similarity: {data['Full Text Similarity']}")

def rank_resumes_by_avg_score(results):
    ranking_data = []
    for resume_name, data in results.items():
        avg_score = data['Average Score']
        full_text_similarity = data['Full Text Similarity']
        combined_score = (avg_score + full_text_similarity) / 2
        ranking_data.append((resume_name, combined_score))
    
    ranking_data.sort(key=lambda x: x[1], reverse = True)
    
    print("Resume Rankings by Average Score:")
    print("=" * 50)
    print(f"{'Rank':<5}{'Resume Name':<40}{'Score':<15}")
    print("-" * 50)

    for rank, (resume_name, score) in enumerate(ranking_data, 1):
        print(f"{rank:<5}{resume_name:<40}{score:<15.4f}")

    return ranking_data

ranked_resumes = rank_resumes_by_avg_score(results)
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from .ml_loader import MLModels

# Sample iGOT Karmayogi course database (in production, fetch from API)
IGOT_COURSES = [
    {
        "id": "IGOT001",
        "title": "Introduction to Data Analysis with Python",
        "category": "technical",
        "skills": ["Python", "Data Analysis", "Data Visualization"],
        "difficulty": "beginner",
        "duration": 120,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/python-data-analysis"
    },
    {
        "id": "IGOT002",
        "title": "Survey Design and Implementation",
        "category": "statistical",
        "skills": ["Survey Design", "Sampling Methods", "Data Collection"],
        "difficulty": "intermediate",
        "duration": 180,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/survey-design"
    },
    {
        "id": "IGOT003",
        "title": "National Accounts and GDP Calculation",
        "category": "statistical",
        "skills": ["National Accounts", "GDP", "Economic Statistics"],
        "difficulty": "intermediate",
        "duration": 150,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/national-accounts"
    },
    {
        "id": "IGOT004",
        "title": "Data Visualization with Tableau",
        "category": "technical",
        "skills": ["Data Visualization", "Tableau", "Business Intelligence"],
        "difficulty": "beginner",
        "duration": 90,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/tableau-visualization"
    },
    {
        "id": "IGOT005",
        "title": "Machine Learning for Statistics",
        "category": "technical",
        "skills": ["Machine Learning", "AI/ML", "Statistical Learning"],
        "difficulty": "advanced",
        "duration": 240,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/ml-statistics"
    },
    {
        "id": "IGOT006",
        "title": "Cybersecurity Fundamentals",
        "category": "digital_governance",
        "skills": ["Cybersecurity", "Information Security", "Data Privacy"],
        "difficulty": "beginner",
        "duration": 60,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/cybersecurity"
    },
    {
        "id": "IGOT007",
        "title": "Effective Communication Skills",
        "category": "behavioural",
        "skills": ["Communication", "Presentation Skills", "Report Writing"],
        "difficulty": "beginner",
        "duration": 45,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/communication"
    },
    {
        "id": "IGOT008",
        "title": "Project Management for Government",
        "category": "behavioural",
        "skills": ["Project Management", "Leadership", "Decision Making"],
        "difficulty": "intermediate",
        "duration": 120,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/project-management"
    },
    {
        "id": "IGOT009",
        "title": "SQL for Data Management",
        "category": "technical",
        "skills": ["SQL", "Database Management", "Data Quality"],
        "difficulty": "beginner",
        "duration": 90,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/sql-database"
    },
    {
        "id": "IGOT010",
        "title": "Price Statistics and CPI",
        "category": "statistical",
        "skills": ["Price Statistics", "CPI", "Inflation Measurement"],
        "difficulty": "intermediate",
        "duration": 100,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/price-statistics"
    },
    {
        "id": "IGOT011",
        "title": "R Programming for Statistical Analysis",
        "category": "technical",
        "skills": ["R", "Statistical Analysis", "Data Analysis"],
        "difficulty": "intermediate",
        "duration": 150,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/r-programming"
    },
    {
        "id": "IGOT012",
        "title": "GIS and Spatial Analysis",
        "category": "technical",
        "skills": ["GIS", "Spatial Analysis", "Mapping"],
        "difficulty": "intermediate",
        "duration": 180,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/gis-spatial"
    },
    {
        "id": "IGOT013",
        "title": "Labour Statistics and Employment Data",
        "category": "statistical",
        "skills": ["Labour Statistics", "Employment Data", "Workforce Analytics"],
        "difficulty": "intermediate",
        "duration": 120,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/labour-statistics"
    },
    {
        "id": "IGOT014",
        "title": "Cloud Computing for Government",
        "category": "digital_governance",
        "skills": ["Cloud Computing", "Government Cloud", "Infrastructure"],
        "difficulty": "intermediate",
        "duration": 90,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/cloud-computing"
    },
    {
        "id": "IGOT015",
        "title": "Ethics in Public Service",
        "category": "behavioural",
        "skills": ["Ethics", "Governance", "Public Service"],
        "difficulty": "beginner",
        "duration": 60,
        "language": "en",
        "url": "https://igotkarmayogi.gov.in/course/ethics-public-service"
    }
]

class RecommendationEngine:
    def __init__(self):
        self.ml = MLModels()
        self.courses = IGOT_COURSES
        self.course_embeddings = None
    
    def _encode_courses(self):
        """Encode course descriptions for semantic search"""
        if self.course_embeddings is None:
            course_texts = [
                f"{c['title']} {' '.join(c['skills'])} {c['category']}"
                for c in self.courses
            ]
            self.course_embeddings = self.ml.skill_encoder.encode(course_texts)
    
    def recommend_courses(self, skill_gaps: List[Dict], 
                          user_profile: Dict = None,
                          num_recommendations: int = 5) -> List[Dict]:
        """Recommend courses based on skill gaps"""
        self._encode_courses()
        
        gap_text = " ".join([gap["skill"] for gap in skill_gaps[:5]])
        gap_embedding = self.ml.skill_encoder.encode([gap_text])[0]
        
        similarities = np.dot(self.course_embeddings, gap_embedding) / (
            np.linalg.norm(self.course_embeddings, axis=1) * np.linalg.norm(gap_embedding)
        )
        
        sorted_indices = np.argsort(similarities)[::-1]
        
        recommendations = []
        for idx in sorted_indices[:num_recommendations]:
            course = self.courses[idx].copy()
            course["relevance_score"] = float(similarities[idx])
            course["matched_skills"] = [
                gap["skill"] for gap in skill_gaps
                if gap["skill"] in course["skills"]
            ]
            recommendations.append(course)
        
        return recommendations
    
    def recommend_by_skill(self, skill_name: str, 
                           current_level: float = 0,
                           num_recommendations: int = 3) -> List[Dict]:
        """Recommend courses for a specific skill"""
        self._encode_courses()
        
        skill_embedding = self.ml.skill_encoder.encode([skill_name])[0]
        
        similarities = np.dot(self.course_embeddings, skill_embedding) / (
            np.linalg.norm(self.course_embeddings, axis=1) * np.linalg.norm(skill_embedding)
        )
        
        sorted_indices = np.argsort(similarities)[::-1]
        
        recommendations = []
        for idx in sorted_indices[:num_recommendations]:
            course = self.courses[idx].copy()
            course["relevance_score"] = float(similarities[idx])
            
            if current_level < 2:
                course["difficulty"] = "beginner"
            elif current_level < 4:
                course["difficulty"] = "intermediate"
            else:
                course["difficulty"] = "advanced"
            
            recommendations.append(course)
        
        return recommendations
    
    def generate_learning_path(self, skill_gaps: List[Dict],
                               user_profile: Dict = None) -> Dict:
        """Generate a complete learning path"""
        all_recommendations = []
        
        for gap in skill_gaps[:5]:
            recs = self.recommend_by_skill(
                gap["skill"],
                current_level=gap["current_level"],
                num_recommendations=2
            )
            all_recommendations.extend(recs)
        
        seen_ids = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec["id"] not in seen_ids:
                seen_ids.add(rec["id"])
                unique_recommendations.append(rec)
        
        priority_order = sorted(
            unique_recommendations,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )
        
        total_duration = sum(c.get("duration", 60) for c in priority_order)
        estimated_days = max(7, total_duration // 60)
        
        return {
            "skill_gaps": skill_gaps,
            "recommended_courses": priority_order,
            "total_courses": len(priority_order),
            "estimated_duration_hours": total_duration // 60,
            "estimated_completion_days": estimated_days,
            "learning_milestones": self._generate_milestones(priority_order)
        }
    
    def _generate_milestones(self, courses: List[Dict]) -> List[Dict]:
        """Generate learning milestones"""
        milestones = []
        
        for i, course in enumerate(courses[:5]):
            milestones.append({
                "milestone": i + 1,
                "course": course["title"],
                "skills_to_gain": course.get("skills", []),
                "estimated_completion": f"Week {i + 1}",
                "checkpoint": f"Complete {course['title']} and pass assessment"
            })
        
        return milestones

import json
from typing import List, Dict, Tuple
from .ml_loader import MLModels

# O*NET-inspired competency framework for India's Official Statistical System
COMPETENCY_FRAMEWORK = {
    "statistical": {
        "skills": [
            "Survey Design", "Sampling Methods", "National Accounts",
            "Price Statistics", "Labour Statistics", "Agricultural Statistics",
            "Industrial Statistics", "SDG Indicators", "Metadata Standards",
            "Data Quality Frameworks", "Statistical Analysis", "Data Collection"
        ],
        "levels": {1: "Basic", 2: "Intermediate", 3: "Proficient", 4: "Advanced", 5: "Expert"}
    },
    "technical": {
        "skills": [
            "Python", "R", "SQL", "Stata", "SPSS", "SAS",
            "GIS", "Data Visualization", "AI/ML", "Cloud Computing",
            "APIs", "Open Data", "Big Data Analytics", "Machine Learning"
        ],
        "levels": {1: "Basic", 2: "Intermediate", 3: "Proficient", 4: "Advanced", 5: "Expert"}
    },
    "digital_governance": {
        "skills": [
            "Cybersecurity", "Data Privacy", "Digital Signatures",
            "Government Cloud", "Digital Public Infrastructure",
            "Information Security", "Compliance", "Risk Management"
        ],
        "levels": {1: "Basic", 2: "Intermediate", 3: "Proficient", 4: "Advanced", 5: "Expert"}
    },
    "behavioural": {
        "skills": [
            "Leadership", "Communication", "Project Management",
            "Ethics", "Decision Making", "Change Management",
            "Team Building", "Problem Solving", "Critical Thinking"
        ],
        "levels": {1: "Basic", 2: "Intermediate", 3: "Proficient", 4: "Advanced", 5: "Expert"}
    }
}

class SkillGapAnalyzer:
    def __init__(self):
        self.ml = MLModels()
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using NLP"""
        doc = self.ml.nlp(text.lower())
        
        extracted_skills = []
        all_skills = []
        for category in COMPETENCY_FRAMEWORK.values():
            all_skills.extend([s.lower() for s in category["skills"]])
        
        for token in doc:
            if token.text in all_skills:
                extracted_skills.append(token.text)
        
        for chunk in doc.noun_chunks:
            chunk_lower = chunk.text.lower()
            for skill in all_skills:
                if skill in chunk_lower or chunk_lower in skill:
                    if skill not in extracted_skills:
                        extracted_skills.append(skill)
        
        return list(set(extracted_skills))
    
    def assess_competency_level(self, user_skills: List[str], user_experience: int) -> Dict[str, float]:
        """Assess competency levels based on skills and experience"""
        competency_levels = {}
        
        for category, data in COMPETENCY_FRAMEWORK.items():
            for skill in data["skills"]:
                if skill.lower() in [s.lower() for s in user_skills]:
                    base_level = min(3.0, 1.0 + (user_experience * 0.3))
                    competency_levels[skill] = min(5.0, base_level)
                else:
                    competency_levels[skill] = 0.0
        
        return competency_levels
    
    def identify_gaps(self, current_levels: Dict[str, float], 
                      target_levels: Dict[str, float] = None) -> List[Dict]:
        """Identify skill gaps between current and target levels"""
        gaps = []
        
        if target_levels is None:
            target_levels = self._get_default_targets()
        
        for skill, current in current_levels.items():
            target = target_levels.get(skill, 3.0)
            if current < target:
                gaps.append({
                    "skill": skill,
                    "current_level": current,
                    "target_level": target,
                    "gap": target - current,
                    "priority": "high" if (target - current) > 2 else "medium" if (target - current) > 1 else "low"
                })
        
        gaps.sort(key=lambda x: x["gap"], reverse=True)
        return gaps
    
    def _get_default_targets(self) -> Dict[str, float]:
        """Get default target levels for government officials"""
        return {
            "Survey Design": 4.0,
            "Sampling Methods": 4.0,
            "National Accounts": 3.5,
            "Price Statistics": 3.5,
            "Python": 3.0,
            "R": 3.0,
            "SQL": 4.0,
            "Data Visualization": 3.5,
            "AI/ML": 2.5,
            "Data Quality Frameworks": 4.0,
            "Leadership": 4.0,
            "Communication": 4.0,
            "Project Management": 3.5,
            "Cybersecurity": 3.0,
            "Data Privacy": 3.5
        }
    
    def generate_competency_report(self, user_id: int, 
                                    user_skills: List[str],
                                    experience: int) -> Dict:
        """Generate comprehensive competency report"""
        current_levels = self.assess_competency_level(user_skills, experience)
        gaps = self.identify_gaps(current_levels)
        
        category_summary = {}
        for category, data in COMPETENCY_FRAMEWORK.items():
            cat_skills = [s for s in data["skills"]]
            cat_levels = [current_levels.get(s, 0) for s in cat_skills]
            category_summary[category] = {
                "average_level": sum(cat_levels) / len(cat_levels) if cat_levels else 0,
                "skills_assessed": len([l for l in cat_levels if l > 0]),
                "total_skills": len(cat_skills)
            }
        
        return {
            "user_id": user_id,
            "competency_levels": current_levels,
            "skill_gaps": gaps,
            "category_summary": category_summary,
            "overall_score": sum(current_levels.values()) / len(current_levels) if current_levels else 0,
            "recommendations": self._generate_recommendations(gaps)
        }
    
    def _generate_recommendations(self, gaps: List[Dict]) -> List[str]:
        """Generate learning recommendations based on gaps"""
        recommendations = []
        
        high_priority = [g for g in gaps if g["priority"] == "high"]
        medium_priority = [g for g in gaps if g["priority"] == "medium"]
        
        if high_priority:
            recommendations.append(
                f"Focus immediately on: {', '.join([g['skill'] for g in high_priority[:3]])}"
            )
        
        if medium_priority:
            recommendations.append(
                f"Plan to improve: {', '.join([g['skill'] for g in medium_priority[:3]])}"
            )
        
        recommendations.append("Consider enrolling in iGOT Karmayogi courses for skill development")
        
        return recommendations

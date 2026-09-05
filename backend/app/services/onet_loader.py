"""O*NET data loader - loads skills and job roles from CSV files into the database."""
import csv
import os
from typing import Dict, List, Tuple


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')


def load_onet_skills() -> Dict[str, List[str]]:
    """Load O*NET skills from CSV files, grouped by category."""
    skills_by_category = {
        "essential": [],
        "software": []
    }

    # Essential skills
    ess_path = os.path.join(DATA_DIR, 'essential_skills.csv')
    if os.path.exists(ess_path):
        with open(ess_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('Element Name', '').strip()
                if name and name not in skills_by_category["essential"]:
                    skills_by_category["essential"].append(name)

    # Software skills
    sw_path = os.path.join(DATA_DIR, 'software_skills.csv')
    if os.path.exists(sw_path):
        with open(sw_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('Element Name', '').strip()
                if name and name not in skills_by_category["software"]:
                    skills_by_category["software"].append(name)

    return skills_by_category


def load_onet_job_roles() -> List[Dict[str, str]]:
    """Load O*NET job roles from CSV."""
    jobs = []
    path = os.path.join(DATA_DIR, 'occupation_data.csv')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get('O*NET-SOC Code', '').strip()
                title = row.get('Title', '').strip()
                desc = row.get('Description', '').strip()
                if code and title:
                    jobs.append({
                        "code": code,
                        "title": title,
                        "description": desc
                    })
    return jobs


def get_skill_category(skill_name: str) -> str:
    """Determine the category of a skill based on O*NET data."""
    technical_keywords = [
        'python', 'r', 'sql', 'stata', 'spss', 'sas', 'gis', 'machine learning',
        'ai', 'cloud', 'data', 'programming', 'software', 'database', 'api',
        'cybersecurity', 'linux', 'java', 'javascript', 'html', 'css', 'react',
        'node', 'docker', 'kubernetes', 'aws', 'azure', 'tensorflow', 'pytorch'
    ]

    soft_keywords = [
        'leadership', 'communication', 'project management', 'ethics', 'decision',
        'team', 'problem solving', 'critical thinking', 'time management',
        'adaptability', 'collaboration', 'negotiation', 'presentation'
    ]

    skill_lower = skill_name.lower()

    for kw in technical_keywords:
        if kw in skill_lower:
            return "technical"

    for kw in soft_keywords:
        if kw in skill_lower:
            return "behavioural"

    return "general"

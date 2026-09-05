from typing import List, Dict, Optional
import httpx
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class IGOTConnector:
    def __init__(self):
        self.base_url = os.getenv("IGOT_API_URL", "https://api.karmayogi.gov.in")
        self.api_key = os.getenv("IGOT_API_KEY", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def get_course_catalog(self, category: str = None) -> List[Dict]:
        """Fetch course catalog from iGOT Karmayogi"""
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/courses",
                    headers=self.headers,
                    params={"category": category} if category else {}
                )
                if response.status_code == 200:
                    courses = response.json().get("courses", [])
                    for c in courses:
                        c["source"] = "live"
                    return courses
                else:
                    logger.warning("iGOT API returned status %d, using mock data", response.status_code)
                    return self._get_mock_courses(category)
            except Exception as e:
                logger.warning("iGOT API unavailable: %s, using mock data", e)
                return self._get_mock_courses(category)

    async def get_user_progress(self, user_id: str) -> Dict:
        """Fetch user progress from iGOT"""
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}/progress",
                    headers=self.headers
                )
                if response.status_code == 200:
                    data = response.json()
                    data["source"] = "live"
                    return data
                else:
                    logger.warning("iGOT progress API returned status %d, using mock data", response.status_code)
                    return self._get_mock_progress()
            except Exception as e:
                logger.warning("iGOT progress API unavailable: %s, using mock data", e)
                return self._get_mock_progress()

    async def enroll_user(self, user_id: str, course_id: str) -> Dict:
        """Enroll user in a course on iGOT"""
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/enrollments",
                    headers=self.headers,
                    json={"user_id": user_id, "course_id": course_id}
                )
                if response.status_code == 200:
                    return {"status": "enrolled", "course_id": course_id, "source": "live"}
                else:
                    logger.warning("iGOT enrollment API returned status %d", response.status_code)
                    return {"status": "enrolled", "course_id": course_id, "source": "demo"}
            except Exception as e:
                logger.warning("iGOT enrollment API unavailable: %s", e)
                return {"status": "enrolled", "course_id": course_id, "source": "demo"}

    async def sync_competencies(self, user_id: str, competencies: Dict) -> Dict:
        """Sync competency data with iGOT"""
        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                response = await client.put(
                    f"{self.base_url}/api/v1/users/{user_id}/competencies",
                    headers=self.headers,
                    json=competencies
                )
                if response.status_code == 200:
                    return {"status": "synced", "source": "live"}
                else:
                    logger.warning("iGOT sync API returned status %d", response.status_code)
                    return {"status": "synced", "source": "demo"}
            except Exception as e:
                logger.warning("iGOT sync API unavailable: %s", e)
                return {"status": "synced", "source": "demo"}

    def get_course_by_id(self, course_id: str) -> Optional[Dict]:
        """Search mock catalog for a specific course by ID"""
        for course in self._get_mock_courses():
            if course["id"] == course_id:
                return course
        return None

    def _get_mock_courses(self, category: str = None) -> List[Dict]:
        """Return rich mock course data for development"""
        courses = [
            {
                "id": "IGOT001",
                "title": "Python for Data Analysis",
                "category": "technical",
                "skills": ["Python", "Data Analysis", "Pandas", "NumPy"],
                "duration": 120,
                "difficulty": "beginner",
                "language": "en",
                "instructor": "Dr. Ananya Sharma",
                "rating": 4.5,
                "enrolled_count": 12500,
                "description": "Learn Python fundamentals for data analysis including Pandas, NumPy, and data wrangling techniques.",
                "source": "demo"
            },
            {
                "id": "IGOT002",
                "title": "Survey Design Fundamentals",
                "category": "statistical",
                "skills": ["Survey Design", "Sampling", "Data Collection"],
                "duration": 180,
                "difficulty": "intermediate",
                "language": "en",
                "instructor": "Prof. Rajesh Kumar",
                "rating": 4.3,
                "enrolled_count": 8200,
                "description": "Master survey methodology, sampling techniques, and questionnaire design for government research.",
                "source": "demo"
            },
            {
                "id": "IGOT003",
                "title": "National Accounts and GDP Calculation",
                "category": "statistical",
                "skills": ["National Accounts", "GDP", "Economic Statistics"],
                "duration": 150,
                "difficulty": "intermediate",
                "language": "en",
                "instructor": "Dr. Meera Joshi",
                "rating": 4.2,
                "enrolled_count": 6700,
                "description": "Understand national income accounting, GDP computation methods, and economic indicator analysis.",
                "source": "demo"
            },
            {
                "id": "IGOT004",
                "title": "Data Visualization with Tableau",
                "category": "technical",
                "skills": ["Data Visualization", "Tableau", "Business Intelligence"],
                "duration": 90,
                "difficulty": "beginner",
                "language": "en",
                "instructor": "Sunita Verma",
                "rating": 4.6,
                "enrolled_count": 15300,
                "description": "Create interactive dashboards and visualizations using Tableau for data-driven decision making.",
                "source": "demo"
            },
            {
                "id": "IGOT005",
                "title": "Machine Learning for Statistics",
                "category": "technical",
                "skills": ["Machine Learning", "AI/ML", "Statistical Learning"],
                "duration": 240,
                "difficulty": "advanced",
                "language": "en",
                "instructor": "Dr. Vikram Patel",
                "rating": 4.7,
                "enrolled_count": 9800,
                "description": "Advanced ML techniques applied to statistical problems including regression, classification, and clustering.",
                "source": "demo"
            },
            {
                "id": "IGOT006",
                "title": "Cybersecurity Fundamentals",
                "category": "digital_governance",
                "skills": ["Cybersecurity", "Information Security", "Data Privacy"],
                "duration": 60,
                "difficulty": "beginner",
                "language": "en",
                "instructor": "Arjun Nair",
                "rating": 4.4,
                "enrolled_count": 22100,
                "description": "Essential cybersecurity concepts, threat identification, and data protection practices for government officials.",
                "source": "demo"
            },
            {
                "id": "IGOT007",
                "title": "Effective Communication Skills",
                "category": "behavioural",
                "skills": ["Communication", "Presentation Skills", "Report Writing"],
                "duration": 45,
                "difficulty": "beginner",
                "language": "en",
                "instructor": "Priya Desai",
                "rating": 4.1,
                "enrolled_count": 18500,
                "description": "Develop professional communication, presentation, and report writing skills for public service.",
                "source": "demo"
            },
            {
                "id": "IGOT008",
                "title": "Project Management for Government",
                "category": "behavioural",
                "skills": ["Project Management", "Leadership", "Decision Making"],
                "duration": 120,
                "difficulty": "intermediate",
                "language": "en",
                "instructor": "Suresh Reddy",
                "rating": 4.3,
                "enrolled_count": 11200,
                "description": "Government-specific project management methodologies, stakeholder management, and execution frameworks.",
                "source": "demo"
            },
            {
                "id": "IGOT009",
                "title": "SQL for Data Management",
                "category": "technical",
                "skills": ["SQL", "Database Management", "Data Quality"],
                "duration": 90,
                "difficulty": "beginner",
                "language": "en",
                "instructor": "Kavita Rao",
                "rating": 4.5,
                "enrolled_count": 20300,
                "description": "SQL fundamentals for querying, managing, and analyzing government databases effectively.",
                "source": "demo"
            },
            {
                "id": "IGOT010",
                "title": "Price Statistics and CPI",
                "category": "statistical",
                "skills": ["Price Statistics", "CPI", "Inflation Measurement"],
                "duration": 100,
                "difficulty": "intermediate",
                "language": "en",
                "instructor": "Dr. Amitabh Gupta",
                "rating": 4.0,
                "enrolled_count": 5400,
                "description": "Consumer Price Index computation, price collection methodology, and inflation analysis.",
                "source": "demo"
            },
            {
                "id": "IGOT011",
                "title": "R Programming for Statistical Analysis",
                "category": "technical",
                "skills": ["R", "Statistical Analysis", "Data Analysis"],
                "duration": 150,
                "difficulty": "intermediate",
                "language": "en",
                "instructor": "Dr. Neha Kapoor",
                "rating": 4.4,
                "enrolled_count": 7600,
                "description": "Statistical computing with R including hypothesis testing, regression, and data visualization with ggplot2.",
                "source": "demo"
            },
            {
                "id": "IGOT012",
                "title": "GIS and Spatial Analysis",
                "category": "technical",
                "skills": ["GIS", "Spatial Analysis", "Mapping"],
                "duration": 180,
                "difficulty": "intermediate",
                "language": "en",
                "instructor": "Prof. Deepak Menon",
                "rating": 4.2,
                "enrolled_count": 4300,
                "description": "Geographic Information Systems for spatial data analysis, mapping, and urban planning applications.",
                "source": "demo"
            },
            {
                "id": "IGOT013",
                "title": "Labour Statistics and Employment Data",
                "category": "statistical",
                "skills": ["Labour Statistics", "Employment Data", "Workforce Analytics"],
                "duration": 120,
                "difficulty": "intermediate",
                "language": "en",
                "instructor": "Dr. Suman Bhat",
                "rating": 4.1,
                "enrolled_count": 3900,
                "description": "Labour force surveys, employment metrics computation, and workforce trend analysis.",
                "source": "demo"
            },
            {
                "id": "IGOT014",
                "title": "Cloud Computing for Government",
                "category": "digital_governance",
                "skills": ["Cloud Computing", "Government Cloud", "Infrastructure"],
                "duration": 90,
                "difficulty": "intermediate",
                "language": "en",
                "instructor": "Raghav Iyer",
                "rating": 4.3,
                "enrolled_count": 10700,
                "description": "Cloud infrastructure for government, MeghRaj guidelines, and secure deployment practices.",
                "source": "demo"
            },
            {
                "id": "IGOT015",
                "title": "Ethics in Public Service",
                "category": "behavioural",
                "skills": ["Ethics", "Governance", "Public Service"],
                "duration": 60,
                "difficulty": "beginner",
                "language": "en",
                "instructor": "Dr. Lakshmi Iyer",
                "rating": 4.6,
                "enrolled_count": 25800,
                "description": "Ethical frameworks, code of conduct, and integrity principles for public servants.",
                "source": "demo"
            },
            {
                "id": "IGOT016",
                "title": "Advanced Excel for Government Reports",
                "category": "technical",
                "skills": ["Excel", "Data Analysis", "Reporting"],
                "duration": 75,
                "difficulty": "beginner",
                "language": "en",
                "instructor": "Anjali Kulkarni",
                "rating": 4.4,
                "enrolled_count": 31200,
                "description": "Advanced Excel features including pivot tables, VLOOKUP, macros, and automated government report generation.",
                "source": "demo"
            },
            {
                "id": "IGOT017",
                "title": "Leadership in Administration",
                "category": "behavioural",
                "skills": ["Leadership", "Team Management", "Conflict Resolution"],
                "duration": 100,
                "difficulty": "advanced",
                "language": "en",
                "instructor": "Gp. Capt. Ravi Shankar (Retd.)",
                "rating": 4.5,
                "enrolled_count": 7100,
                "description": "Leadership principles for government administrators including team building and crisis management.",
                "source": "demo"
            },
            {
                "id": "IGOT018",
                "title": "Blockchain for Governance",
                "category": "digital_governance",
                "skills": ["Blockchain", "Distributed Systems", "Smart Contracts"],
                "duration": 130,
                "difficulty": "advanced",
                "language": "en",
                "instructor": "Dr. Priyadarshi Mohapatra",
                "rating": 4.2,
                "enrolled_count": 3400,
                "description": "Blockchain applications in government: land records, supply chain, digital identity, and smart contracts.",
                "source": "demo"
            },
            {
                "id": "IGOT019",
                "title": "Big Data Analytics with Hadoop",
                "category": "technical",
                "skills": ["Big Data", "Hadoop", "Spark", "Data Engineering"],
                "duration": 200,
                "difficulty": "advanced",
                "language": "en",
                "instructor": "Dr. Tarun Bhargava",
                "rating": 4.3,
                "enrolled_count": 5900,
                "description": "Processing and analyzing large-scale government datasets using Hadoop, Spark, and distributed computing.",
                "source": "demo"
            },
            {
                "id": "IGOT020",
                "title": "Population Census Data Analysis",
                "category": "statistical",
                "skills": ["Census Data", "Demography", "Population Statistics"],
                "duration": 140,
                "difficulty": "intermediate",
                "language": "en",
                "instructor": "Dr. Shalini Sharma",
                "rating": 4.1,
                "enrolled_count": 4100,
                "description": "Analysis of census data, demographic trends, and population projection methodologies.",
                "source": "demo"
            },
            {
                "id": "IGOT021",
                "title": "Digital India Initiatives Overview",
                "category": "digital_governance",
                "skills": ["Digital Governance", "e-Governance", "Citizen Services"],
                "duration": 50,
                "difficulty": "beginner",
                "language": "en",
                "instructor": "Aruna Sundararajan",
                "rating": 4.7,
                "enrolled_count": 34500,
                "description": "Comprehensive overview of Digital India initiatives, e-governance platforms, and citizen service delivery.",
                "source": "demo"
            },
            {
                "id": "IGOT022",
                "title": "Stress Management and Wellbeing",
                "category": "behavioural",
                "skills": ["Stress Management", "Wellbeing", "Work-Life Balance"],
                "duration": 40,
                "difficulty": "beginner",
                "language": "en",
                "instructor": "Dr. Rajiv Chavan",
                "rating": 4.8,
                "enrolled_count": 28700,
                "description": "Practical techniques for managing workplace stress, mindfulness, and maintaining work-life balance.",
                "source": "demo"
            },
            {
                "id": "IGOT023",
                "title": "Artificial Intelligence for Public Policy",
                "category": "digital_governance",
                "skills": ["AI/ML", "Public Policy", "Algorithmic Governance"],
                "duration": 160,
                "difficulty": "advanced",
                "language": "en",
                "instructor": "Dr. Shashi Shekhar",
                "rating": 4.4,
                "enrolled_count": 6200,
                "description": "Application of AI/ML in public policy design, algorithmic accountability, and automated decision systems.",
                "source": "demo"
            },
            {
                "id": "IGOT024",
                "title": "Financial Management in Government",
                "category": "statistical",
                "skills": ["Financial Analysis", "Budgeting", "Public Finance"],
                "duration": 110,
                "difficulty": "intermediate",
                "language": "en",
                "instructor": "CA Prakash Dhavan",
                "rating": 4.3,
                "enrolled_count": 9100,
                "description": "Government financial management, budget preparation, expenditure tracking, and audit compliance.",
                "source": "demo"
            }
        ]

        if category:
            courses = [c for c in courses if c["category"] == category]
        return courses

    def _get_mock_progress(self) -> Dict:
        """Return mock progress data for development"""
        return {
            "courses_completed": 5,
            "courses_in_progress": 2,
            "total_learning_hours": 24,
            "competencies_gained": ["Python", "Data Analysis", "SQL"],
            "badges_earned": ["Quick Learner", "Data Explorer"],
            "streak_days": 12,
            "last_activity": datetime.utcnow().isoformat(),
            "source": "demo"
        }

"""Load O*NET data into the database."""
import csv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import SessionLocal, engine
from app.models.models import Base, Skill, JobRole, SkillDemand


def load_data():
    """Load O*NET CSVs into database tables."""
    db = SessionLocal()
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Check if data already loaded
        if db.query(Skill).count() > 0:
            print("Data already loaded. Skipping.")
            return

        data_dir = os.path.join(os.path.dirname(__file__), 'data')

        # Load skills from essential_skills.csv
        print("Loading skills from essential_skills.csv...")
        skills_map = {}
        with open(os.path.join(data_dir, 'essential_skills.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                skill_name = row.get('Element Name', '').strip()
                if skill_name and skill_name not in skills_map:
                    skills_map[skill_name] = skill_name

        # Also add software skills
        print("Loading skills from software_skills.csv...")
        with open(os.path.join(data_dir, 'software_skills.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                skill_name = row.get('Element Name', '').strip()
                if skill_name and skill_name not in skills_map:
                    skills_map[skill_name] = skill_name

        # Insert skills
        for name in skills_map:
            skill = Skill(name=name, category="General")
            db.add(skill)
        db.commit()
        print(f"Loaded {len(skills_map)} skills")

        # Load job roles from occupation_data.csv
        print("Loading job roles from occupation_data.csv...")
        jobs_map = {}
        with open(os.path.join(data_dir, 'occupation_data.csv'), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get('O*NET-SOC Code', '').strip()
                title = row.get('Title', '').strip()
                desc = row.get('Description', '').strip()
                if code and title:
                    jobs_map[code] = {'title': title, 'description': desc}

        # Insert job roles
        for code, data in jobs_map.items():
            role = JobRole(title=data['title'], description=data['description'], sector="General")
            db.add(role)
        db.commit()
        print(f"Loaded {len(jobs_map)} job roles")

        print("Data loading complete!")

    except Exception as e:
        print(f"Error loading data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_data()

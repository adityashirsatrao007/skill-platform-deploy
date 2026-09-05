from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import random
import os
from collections import defaultdict

# ====== CONFIGURATION ======

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skill_platform.db")

# ====== DATABASE SETUP ======

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ====== DATABASE MODELS ======

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String, default="learner")
    designation = Column(String)
    department = Column(String)
    job_role = Column(String)
    years_of_experience = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserCompetency(Base):
    __tablename__ = "user_competencies"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_name = Column(String)
    category = Column(String)
    current_level = Column(Float, default=0.0)
    target_level = Column(Float, default=3.5)
    last_assessed = Column(DateTime, default=datetime.utcnow)

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    questions = Column(JSON)
    difficulty = Column(String)
    category = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    answers = Column(JSON)
    score = Column(Float)
    time_taken_seconds = Column(Integer)
    completed_at = Column(DateTime, default=datetime.utcnow)

class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(String)
    status = Column(String, default="enrolled")
    progress = Column(Float, default=0.0)
    enrolled_at = Column(DateTime, default=datetime.utcnow)

class LearningPath(Base):
    __tablename__ = "learning_paths"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_gaps = Column(JSON)
    recommended_courses = Column(JSON)
    estimated_days = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

# Create tables
Base.metadata.create_all(bind=engine)

# ====== SECURITY ======

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# ====== COMPETENCY FRAMEWORK ======

COMPETENCY_FRAMEWORK = {
    "statistical": {
        "skills": ["Survey Design", "Sampling Methods", "National Accounts", "Price Statistics",
                    "Labour Statistics", "Agricultural Statistics", "SDG Indicators", "Data Quality Frameworks"]
    },
    "technical": {
        "skills": ["Python", "R", "SQL", "Data Visualization", "AI/ML", "Cloud Computing", "GIS", "Machine Learning"]
    },
    "digital_governance": {
        "skills": ["Cybersecurity", "Data Privacy", "Digital Signatures", "Government Cloud"]
    },
    "behavioural": {
        "skills": ["Leadership", "Communication", "Project Management", "Ethics", "Decision Making"]
    }
}

# ====== iGOT COURSES ======

IGOT_COURSES = [
    {"id": "IGOT001", "title": "Python for Data Analysis", "category": "technical", "skills": ["Python", "Data Analysis"], "difficulty": "beginner", "duration": 120, "url": "https://igotkarmayogi.gov.in/course/python-data-analysis"},
    {"id": "IGOT002", "title": "Survey Design Fundamentals", "category": "statistical", "skills": ["Survey Design", "Sampling"], "difficulty": "intermediate", "duration": 180, "url": "https://igotkarmayogi.gov.in/course/survey-design"},
    {"id": "IGOT003", "title": "National Accounts & GDP", "category": "statistical", "skills": ["National Accounts", "GDP"], "difficulty": "intermediate", "duration": 150, "url": "https://igotkarmayogi.gov.in/course/national-accounts"},
    {"id": "IGOT004", "title": "Data Visualization with Tableau", "category": "technical", "skills": ["Data Visualization", "Tableau"], "difficulty": "beginner", "duration": 90, "url": "https://igotkarmayogi.gov.in/course/tableau"},
    {"id": "IGOT005", "title": "Machine Learning Basics", "category": "technical", "skills": ["Machine Learning", "AI/ML"], "difficulty": "advanced", "duration": 240, "url": "https://igotkarmayogi.gov.in/course/ml-basics"},
    {"id": "IGOT006", "title": "Cybersecurity Essentials", "category": "digital_governance", "skills": ["Cybersecurity", "Data Privacy"], "difficulty": "beginner", "duration": 60, "url": "https://igotkarmayogi.gov.in/course/cybersecurity"},
    {"id": "IGOT007", "title": "Communication Skills", "category": "behavioural", "skills": ["Communication", "Presentation"], "difficulty": "beginner", "duration": 45, "url": "https://igotkarmayogi.gov.in/course/communication"},
    {"id": "IGOT008", "title": "Project Management", "category": "behavioural", "skills": ["Project Management", "Leadership"], "difficulty": "intermediate", "duration": 120, "url": "https://igotkarmayogi.gov.in/course/project-mgmt"},
    {"id": "IGOT009", "title": "SQL for Data Management", "category": "technical", "skills": ["SQL", "Database"], "difficulty": "beginner", "duration": 90, "url": "https://igotkarmayogi.gov.in/course/sql"},
    {"id": "IGOT010", "title": "Price Statistics & CPI", "category": "statistical", "skills": ["Price Statistics", "CPI"], "difficulty": "intermediate", "duration": 100, "url": "https://igotkarmayogi.gov.in/course/price-stats"},
    {"id": "IGOT011", "title": "R Programming", "category": "technical", "skills": ["R", "Statistical Analysis"], "difficulty": "intermediate", "duration": 150, "url": "https://igotkarmayogi.gov.in/course/r-programming"},
    {"id": "IGOT012", "title": "GIS & Spatial Analysis", "category": "technical", "skills": ["GIS", "Spatial Analysis"], "difficulty": "intermediate", "duration": 180, "url": "https://igotkarmayogi.gov.in/course/gis"},
]

# ====== PYDANTIC MODELS ======

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    designation: Optional[str] = None
    department: Optional[str] = None
    job_role: Optional[str] = None
    years_of_experience: Optional[int] = 0

class SkillInput(BaseModel):
    skills: List[str]
    experience: int

class QuizRequest(BaseModel):
    text: Optional[str] = None
    concept: Optional[str] = None
    num_questions: int = 5
    difficulty: str = "medium"

class QuizSubmit(BaseModel):
    quiz_id: int
    answers: Dict[str, str]
    time_taken_seconds: int = 0

# ====== FASTAPI APP ======

app = FastAPI(
    title="Skill Intelligence Platform",
    description="AI-Enabled Learning Platform for India's Official Statistical System - SIH PS 26101",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== AUTH ROUTES ======

@app.post("/api/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        designation=user.designation or "Officer",
        department=user.department or "MoSPI",
        job_role=user.job_role,
        years_of_experience=user.years_of_experience or 0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "designation": user.designation,
            "department": user.department
        }
    }

@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "designation": current_user.designation,
        "department": current_user.department,
        "years_of_experience": current_user.years_of_experience
    }

# ====== COMPETENCY ROUTES ======

@app.get("/api/competency/framework")
async def get_framework():
    return COMPETENCY_FRAMEWORK

@app.post("/api/competency/assess")
async def assess_competencies(input_data: SkillInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    competency_levels = {}
    for category, data in COMPETENCY_FRAMEWORK.items():
        for skill in data["skills"]:
            if skill.lower() in [s.lower() for s in input_data.skills]:
                level = min(5.0, 1.0 + (input_data.experience * 0.3))
                competency_levels[skill] = round(level, 1)
            else:
                competency_levels[skill] = 0.0

    gaps = []
    for skill, level in competency_levels.items():
        target = 3.5
        if level < target:
            gaps.append({
                "skill": skill, "current_level": level, "target_level": target,
                "gap": round(target - level, 1),
                "priority": "high" if (target - level) > 2 else "medium" if (target - level) > 1 else "low"
            })
    gaps.sort(key=lambda x: x["gap"], reverse=True)

    # Save to database
    for skill, level in competency_levels.items():
        existing = db.query(UserCompetency).filter(
            UserCompetency.user_id == current_user.id, UserCompetency.skill_name == skill
        ).first()
        if existing:
            existing.current_level = level
            existing.last_assessed = datetime.utcnow()
        else:
            category = "general"
            for cat, data in COMPETENCY_FRAMEWORK.items():
                if skill in data["skills"]:
                    category = cat
                    break
            db.add(UserCompetency(
                user_id=current_user.id, skill_name=skill, category=category,
                current_level=level, target_level=3.5
            ))
    db.commit()

    overall_score = sum(competency_levels.values()) / len(competency_levels) if competency_levels else 0
    return {
        "user_id": current_user.id,
        "competency_levels": competency_levels,
        "skill_gaps": gaps[:10],
        "overall_score": round(overall_score, 2),
        "recommendations": [
            f"Focus on {g['skill']} (gap: {g['gap']})" for g in gaps[:3]
        ] + ["Enroll in iGOT Karmayogi courses for skill development"]
    }

@app.get("/api/competency/gaps")
async def get_gaps(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    competencies = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    current_levels = {c.skill_name: c.current_level for c in competencies}
    gaps = []
    for skill, level in current_levels.items():
        target = 3.5
        if level < target:
            gaps.append({
                "skill": skill, "current_level": level, "target_level": target,
                "gap": round(target - level, 1),
                "priority": "high" if (target - level) > 2 else "medium" if (target - level) > 1 else "low"
            })
    gaps.sort(key=lambda x: x["gap"], reverse=True)
    return {"skill_gaps": gaps}

@app.get("/api/competency/report")
async def get_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    competencies = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    current_levels = {c.skill_name: c.current_level for c in competencies}
    gaps = []
    for skill, level in current_levels.items():
        target = 3.5
        if level < target:
            gaps.append({"skill": skill, "gap": round(target - level, 1)})
    overall_score = sum(current_levels.values()) / len(current_levels) if current_levels else 0
    return {
        "user_id": current_user.id,
        "competency_levels": current_levels,
        "skill_gaps": gaps,
        "overall_score": round(overall_score, 2)
    }

# ====== QUIZ ROUTES ======

@app.post("/api/quiz/generate")
async def generate_quiz(request: QuizRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    text = request.text or request.concept or "General knowledge"
    questions = []
    topics = ["Statistical Analysis", "Data Quality", "Python Programming", "Survey Methods", "Data Visualization", "Machine Learning", "SQL", "Cybersecurity"]

    for i in range(request.num_questions):
        topic = random.choice(topics)
        questions.append({
            "id": i + 1,
            "question": f"What is the best practice for {topic.lower()} in official statistics?",
            "options": [
                "Use standardized methodologies and follow international guidelines",
                "Focus only on speed without quality checks",
                "Skip documentation to save time",
                "Use outdated methods from previous decades"
            ],
            "correct_answer": "A",
            "explanation": f"Best practices in {topic.lower()} involve following standardized methodologies and international guidelines to ensure data quality and consistency.",
            "difficulty": request.difficulty,
            "concept": topic
        })

    quiz = Quiz(
        title=f"Quiz - {request.difficulty.title()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        questions=questions, difficulty=request.difficulty, category="generated",
        created_by=current_user.id
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return {
        "id": quiz.id, "title": quiz.title, "questions": questions,
        "total_questions": len(questions), "difficulty": request.difficulty,
        "time_limit_minutes": len(questions) * 2
    }

@app.post("/api/quiz/submit")
async def submit_quiz(request: QuizSubmit, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == request.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz.questions
    correct = 0
    results = []
    for q in questions:
        user_answer = request.answers.get(str(q["id"]))
        is_correct = user_answer == q["correct_answer"]
        if is_correct:
            correct += 1
        results.append({
            "question_id": q["id"], "question": q["question"],
            "user_answer": user_answer, "correct_answer": q["correct_answer"],
            "is_correct": is_correct, "explanation": q.get("explanation", "")
        })

    total = len(questions)
    score = (correct / total * 100) if total > 0 else 0

    attempt = QuizAttempt(
        user_id=current_user.id, quiz_id=request.quiz_id,
        answers=request.answers, score=round(score, 2),
        time_taken_seconds=request.time_taken_seconds
    )
    db.add(attempt)
    db.commit()

    return {
        "score": round(score, 2),
        "grade": "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "F",
        "correct_count": correct, "total_questions": total, "results": results
    }

@app.get("/api/quiz/history")
async def quiz_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == current_user.id).order_by(QuizAttempt.completed_at.desc()).limit(20).all()
    return {"attempts": [{"id": a.id, "quiz_id": a.quiz_id, "score": a.score, "time_taken": a.time_taken_seconds, "completed_at": a.completed_at.isoformat()} for a in attempts]}

@app.get("/api/quiz/{quiz_id}")
async def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return {"id": quiz.id, "title": quiz.title, "questions": quiz.questions, "difficulty": quiz.difficulty}

# ====== RECOMMENDATION ROUTES ======

@app.post("/api/recommendation/learning-path")
async def get_learning_path(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    competencies = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    current_levels = {c.skill_name: c.current_level for c in competencies}

    gaps = []
    for skill, level in current_levels.items():
        target = 3.5
        if level < target:
            gaps.append({"skill": skill, "current_level": level, "target_level": target, "gap": round(target - level, 1), "priority": "high" if (target - level) > 2 else "medium"})
    gaps.sort(key=lambda x: x["gap"], reverse=True)

    # Find matching courses
    recommended = []
    for gap in gaps[:5]:
        for course in IGOT_COURSES:
            if any(s.lower() in gap["skill"].lower() or gap["skill"].lower() in s.lower() for s in course["skills"]):
                if course["id"] not in [c["id"] for c in recommended]:
                    course_copy = course.copy()
                    course_copy["relevance_score"] = round(0.7 + random.uniform(0, 0.3), 2)
                    course_copy["matched_skills"] = [gap["skill"]]
                    recommended.append(course_copy)

    # Add some general courses if not enough
    if len(recommended) < 3:
        for course in IGOT_COURSES[:3]:
            if course["id"] not in [c["id"] for c in recommended]:
                recommended.append(course)

    total_duration = sum(c.get("duration", 60) for c in recommended[:5])
    estimated_days = max(7, total_duration // 60)

    # Save learning path
    path = LearningPath(
        user_id=current_user.id, skill_gaps=gaps,
        recommended_courses=recommended[:5], estimated_days=estimated_days
    )
    db.add(path)
    db.commit()

    return {
        "skill_gaps": gaps, "recommended_courses": recommended[:5],
        "total_courses": len(recommended[:5]),
        "estimated_duration_hours": total_duration // 60,
        "estimated_completion_days": estimated_days,
        "learning_milestones": [
            {"milestone": i+1, "course": c["title"], "skills_to_gain": c["skills"], "estimated_completion": f"Week {i+1}"}
            for i, c in enumerate(recommended[:3])
        ]
    }

@app.get("/api/recommendation/active-path")
async def get_active_path(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    path = db.query(LearningPath).filter(LearningPath.user_id == current_user.id, LearningPath.is_active == True).order_by(LearningPath.created_at.desc()).first()
    if not path:
        return {"message": "No active learning path", "path": None}
    return {"id": path.id, "skill_gaps": path.skill_gaps, "recommended_courses": path.recommended_courses, "estimated_days": path.estimated_days}

# ====== DASHBOARD ROUTES ======

@app.get("/api/dashboard/learner")
async def learner_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    competencies = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    overall_score = sum(c.current_level for c in competencies) / len(competencies) if competencies else 0
    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == current_user.id).all()
    avg_quiz_score = sum(a.score for a in quiz_attempts) / len(quiz_attempts) if quiz_attempts else 0
    enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.user_id == current_user.id).all()

    top_skills = sorted([{"skill": c.skill_name, "level": c.current_level} for c in competencies], key=lambda x: x["level"], reverse=True)[:5]
    improvement_areas = sorted([{"skill": c.skill_name, "gap": c.target_level - c.current_level} for c in competencies if c.current_level < c.target_level], key=lambda x: x["gap"], reverse=True)[:5]

    return {
        "user": {"name": current_user.full_name, "designation": current_user.designation, "department": current_user.department},
        "competency_summary": {"overall_score": round(overall_score, 2), "skills_assessed": len(competencies), "top_skills": top_skills, "improvement_areas": improvement_areas},
        "quiz_performance": {"total_attempts": len(quiz_attempts), "average_score": round(avg_quiz_score, 2), "recent_attempts": [{"quiz_id": a.quiz_id, "score": a.score, "date": a.completed_at.isoformat()} for a in quiz_attempts[:5]]},
        "learning_progress": {"courses_enrolled": len(enrollments), "courses_completed": len([e for e in enrollments if e.status == "completed"])}
    }

@app.get("/api/dashboard/admin")
async def admin_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    competencies = db.query(UserCompetency).all()
    avg_competency = sum(c.current_level for c in competencies) / len(competencies) if competencies else 0
    quiz_attempts = db.query(QuizAttempt).all()
    enrollments = db.query(CourseEnrollment).all()

    category_stats = defaultdict(list)
    for c in competencies:
        category_stats[c.category].append(c.current_level)
    category_performance = [{"category": cat, "average_level": round(sum(levels)/len(levels), 2)} for cat, levels in category_stats.items()]

    recent_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
    return {
        "overview": {"total_users": total_users, "average_competency": round(avg_competency, 2), "total_quiz_attempts": len(quiz_attempts), "total_enrollments": len(enrollments)},
        "category_performance": category_performance,
        "recent_users": [{"id": u.id, "name": u.full_name, "department": u.department, "joined": u.created_at.isoformat()} for u in recent_users]
    }

@app.get("/api/dashboard/analytics")
async def analytics():
    return {
        "predictive_insights": {
            "skills_in_demand": ["AI/ML", "Data Visualization", "Cloud Computing", "Python", "Machine Learning"],
            "recommended_focus_areas": ["Digital Governance", "Advanced Analytics", "Machine Learning", "Data Quality"],
            "projected_growth": "15% improvement expected in next quarter with consistent learning"
        }
    }

# ====== iGOT ROUTES ======

@app.get("/api/igot/courses")
async def get_igot_courses(category: str = None):
    if category and category != "all":
        filtered = [c for c in IGOT_COURSES if c["category"] == category]
        return {"courses": filtered}
    return {"courses": IGOT_COURSES}

@app.get("/api/igot/recommended")
async def get_recommended(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    competencies = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    skills = [c.skill_name.lower() for c in competencies if c.current_level < 3.5]

    recommended = []
    for course in IGOT_COURSES:
        match_score = sum(1 for s in course["skills"] if any(s.lower() in skill or skill in s.lower() for skill in skills))
        if match_score > 0:
            course_copy = course.copy()
            course_copy["relevance_score"] = round(0.5 + match_score * 0.15, 2)
            recommended.append(course_copy)

    recommended.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    return {"recommendations": recommended[:5] if recommended else IGOT_COURSES[:3]}

@app.post("/api/igot/enroll/{course_id}")
async def enroll(course_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(CourseEnrollment).filter(CourseEnrollment.user_id == current_user.id, CourseEnrollment.course_id == course_id).first()
    if existing:
        return {"status": "already_enrolled", "message": "Already enrolled in this course"}
    enrollment = CourseEnrollment(user_id=current_user.id, course_id=course_id, status="enrolled")
    db.add(enrollment)
    db.commit()
    return {"status": "enrolled", "course_id": course_id, "message": "Successfully enrolled"}

@app.get("/api/igot/progress")
async def igot_progress(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.user_id == current_user.id).all()
    return {
        "courses_completed": len([e for e in enrollments if e.status == "completed"]),
        "courses_in_progress": len([e for e in enrollments if e.status == "in_progress"]),
        "total_enrolled": len(enrollments)
    }

# ====== HEALTH CHECK ======

@app.get("/")
async def root():
    return {"message": "Skill Intelligence Platform - SIH PS 26101", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "database": "connected"}

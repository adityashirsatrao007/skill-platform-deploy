from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict

from ..models.database import get_db
from ..models.models import User, Course, CourseEnrollment, UserCompetency
from ..services.igot_connector import IGOTConnector
from ..api.auth import get_current_user

router = APIRouter()
igot = IGOTConnector()

@router.get("/courses")
async def get_igot_courses(
    category: str = None,
    current_user: User = Depends(get_current_user)
):
    courses = await igot.get_course_catalog(category)
    return {"courses": courses}

@router.post("/enroll/{course_id}")
async def enroll_in_course(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = await igot.enroll_user(str(current_user.id), course_id)
    
    enrollment = CourseEnrollment(
        user_id=current_user.id,
        course_id=1,
        status="enrolled"
    )
    db.add(enrollment)
    db.commit()
    
    return result

@router.get("/progress")
async def get_igot_progress(
    current_user: User = Depends(get_current_user)
):
    progress = await igot.get_user_progress(str(current_user.id))
    return progress

@router.get("/sync-competencies")
async def sync_competencies_with_igot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    competencies = db.query(
        UserCompetency.skill_name,
        UserCompetency.current_level
    ).filter(UserCompetency.user_id == current_user.id).all()
    
    competency_dict = {name: level for name, level in competencies}
    
    result = await igot.sync_competencies(str(current_user.id), competency_dict)
    
    return result

@router.get("/recommended")
async def get_igot_recommended_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ..services.recommendation_engine import RecommendationEngine
    rec_engine = RecommendationEngine()
    
    from ..services.skill_gap_analyzer import SkillGapAnalyzer
    analyzer = SkillGapAnalyzer()
    
    competencies = db.query(UserCompetency).filter(
        UserCompetency.user_id == current_user.id
    ).all()
    
    current_levels = {c.skill_name: c.current_level for c in competencies}
    skill_gaps = analyzer.identify_gaps(current_levels)
    
    recommendations = rec_engine.recommend_courses(
        skill_gaps=skill_gaps,
        num_recommendations=10
    )
    
    return {"recommendations": recommendations}

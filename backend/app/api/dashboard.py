from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List

from ..models.database import get_db
from ..models.models import User, UserCompetency, QuizAttempt, CourseEnrollment, LearningPath
from ..api.auth import get_current_user
from ..services.cache import CacheService

router = APIRouter()
cache = CacheService()


@router.get("/learner")
async def get_learner_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cache_key = f"dashboard:learner:{current_user.id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    competencies = db.query(UserCompetency).filter(
        UserCompetency.user_id == current_user.id
    ).all()

    total_score = sum(c.current_level for c in competencies) / len(competencies) if competencies else 0

    quiz_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id
    ).all()

    avg_quiz_score = sum(a.score for a in quiz_attempts) / len(quiz_attempts) if quiz_attempts else 0

    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.user_id == current_user.id
    ).all()

    active_path = db.query(LearningPath).filter(
        LearningPath.user_id == current_user.id,
        LearningPath.is_active == True
    ).first()

    recent_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id
    ).order_by(QuizAttempt.completed_at.desc()).limit(5).all()

    result = {
        "user": {
            "name": current_user.full_name,
            "designation": current_user.designation,
            "department": current_user.department
        },
        "competency_summary": {
            "overall_score": round(total_score, 2),
            "skills_assessed": len(competencies),
            "top_skills": sorted(
                [{"skill": c.skill_name, "level": c.current_level} for c in competencies],
                key=lambda x: x["level"],
                reverse=True
            )[:5],
            "improvement_areas": sorted(
                [{"skill": c.skill_name, "gap": c.target_level - c.current_level} for c in competencies],
                key=lambda x: x["gap"],
                reverse=True
            )[:5]
        },
        "quiz_performance": {
            "total_attempts": len(quiz_attempts),
            "average_score": round(avg_quiz_score, 2),
            "recent_attempts": [
                {
                    "quiz_id": a.quiz_id,
                    "score": a.score,
                    "date": a.completed_at
                }
                for a in recent_attempts
            ]
        },
        "learning_progress": {
            "courses_enrolled": len(enrollments),
            "courses_completed": len([e for e in enrollments if e.status == "completed"]),
            "active_learning_path": {
                "total_courses": len(active_path.recommended_courses) if active_path else 0,
                "estimated_days": active_path.estimated_completion_days if active_path else 0
            } if active_path else None
        }
    }

    cache.set(cache_key, result, ttl=60)
    return result


@router.get("/admin")
async def get_admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cached = cache.get("dashboard:admin")
    if cached:
        return cached

    total_users = db.query(func.count(User.id)).scalar()

    competencies = db.query(UserCompetency).all()
    avg_competency = sum(c.current_level for c in competencies) / len(competencies) if competencies else 0

    category_stats = db.query(
        UserCompetency.category,
        func.avg(UserCompetency.current_level)
    ).group_by(UserCompetency.category).all()

    quiz_stats = db.query(
        func.count(QuizAttempt.id),
        func.avg(QuizAttempt.score)
    ).first()

    enrollment_stats = db.query(
        func.count(CourseEnrollment.id),
        func.count(CourseEnrollment.id.filter(CourseEnrollment.status == "completed"))
    ).first()

    recent_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()

    skill_distribution = db.query(
        UserCompetency.skill_name,
        func.avg(UserCompetency.current_level),
        func.count(UserCompetency.id)
    ).group_by(UserCompetency.skill_name).all()

    result = {
        "overview": {
            "total_users": total_users,
            "average_competency": round(avg_competency, 2),
            "total_quiz_attempts": quiz_stats[0] or 0,
            "average_quiz_score": round(quiz_stats[1] or 0, 2),
            "total_enrollments": enrollment_stats[0] or 0,
            "courses_completed": enrollment_stats[1] or 0
        },
        "category_performance": [
            {"category": cat, "average_level": round(level, 2)}
            for cat, level in category_stats
        ],
        "skill_distribution": [
            {"skill": skill, "average_level": round(level, 2), "count": count}
            for skill, level, count in skill_distribution
        ],
        "recent_users": [
            {
                "id": u.id,
                "name": u.full_name,
                "department": u.department,
                "joined": u.created_at
            }
            for u in recent_users
        ]
    }

    cache.set("dashboard:admin", result, ttl=120)
    return result


@router.get("/analytics")
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cached = cache.get("dashboard:analytics")
    if cached:
        return cached

    monthly_enrollments = db.query(
        func.date_trunc('month', CourseEnrollment.enrolled_at),
        func.count(CourseEnrollment.id)
    ).group_by(func.date_trunc('month', CourseEnrollment.enrolled_at)).all()

    competency_trends = db.query(
        UserCompetency.skill_name,
        func.avg(UserCompetency.current_level)
    ).group_by(UserCompetency.skill_name).order_by(
        func.avg(UserCompetency.current_level).desc()
    ).limit(10).all()

    competencies = db.query(UserCompetency).all()
    quiz_attempts = db.query(QuizAttempt).all()
    category_stats = db.query(
        UserCompetency.category,
        func.avg(UserCompetency.current_level)
    ).group_by(UserCompetency.category).all()

    avg_competency = sum(c.current_level for c in competencies) / len(competencies) if competencies else 0

    result = {
        "monthly_enrollments": [
            {"month": str(month), "count": count}
            for month, count in monthly_enrollments
        ],
        "top_skills": [
            {"skill": skill, "average_level": round(level, 2)}
            for skill, level in competency_trends
        ],
        "department_wise": [],
        "predictive_insights": {
            "skills_in_demand": [s for s, _ in competency_trends[:5]] if competency_trends else ["AI/ML", "Python", "SQL"],
            "recommended_focus_areas": [cat for cat, _ in category_stats if avg_competency < 3.0] if category_stats else ["Digital Governance"],
            "projected_growth": f"{min(25, max(5, int((avg_competency / 5.0) * 30)))}% improvement projected with consistent learning" if competencies else "Complete assessment to see projections",
            "learning_velocity": f"{len(quiz_attempts)} quizzes completed" if quiz_attempts else "Start taking quizzes to track velocity"
        }
    }

    cache.set("dashboard:analytics", result, ttl=300)
    return result

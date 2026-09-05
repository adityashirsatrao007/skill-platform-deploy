from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
import random

from ..models.database import get_db
from ..models.models import User, Quiz, QuizAttempt
from ..services.mcq_generator import MCQGenerator
from ..services.document_processor import DocumentProcessor
from ..services.onet_loader import load_onet_skills, get_skill_category
from ..api.auth import get_current_user

router = APIRouter()
mcq_generator = MCQGenerator()
doc_processor = DocumentProcessor()

class QuizGenerateRequest(BaseModel):
    text: Optional[str] = None
    concept: Optional[str] = None
    num_questions: int = 5
    difficulty: str = "medium"
    title: Optional[str] = "Generated Quiz"

class SkillQuizRequest(BaseModel):
    skill: str
    num_questions: int = 5
    difficulty: str = "medium"

class QuizSubmitRequest(BaseModel):
    quiz_id: int
    answers: Dict[str, str]
    time_taken_seconds: int

class QuestionResponse(BaseModel):
    id: int
    question: str
    options: List[str]
    difficulty: str
    concept: str

class QuizResponse(BaseModel):
    id: int
    title: str
    questions: List[QuestionResponse]
    total_questions: int
    difficulty: str
    time_limit_minutes: int

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if request.text:
        mcqs = mcq_generator.generate_mcqs_from_text(
            request.text,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
    elif request.concept:
        mcqs = mcq_generator.generate_mcqs_from_concept(
            request.concept,
            num_questions=request.num_questions
        )
    else:
        raise HTTPException(status_code=400, detail="Either text or concept is required")
    
    quiz = Quiz(
        title=request.title,
        questions=mcqs,
        difficulty=request.difficulty,
        category="general",
        created_by=current_user.id
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    return QuizResponse(
        id=quiz.id,
        title=quiz.title,
        questions=[QuestionResponse(**q) for q in mcqs],
        total_questions=len(mcqs),
        difficulty=request.difficulty,
        time_limit_minutes=len(mcqs) * 2
    )

@router.post("/generate-from-skill", response_model=QuizResponse)
async def generate_quiz_from_skill(
    request: SkillQuizRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a quiz based on a specific O*NET skill."""
    onet_skills = load_onet_skills()
    all_skills = []
    for skills in onet_skills.values():
        all_skills.extend(skills)

    skill_name = request.skill
    matched = [s for s in all_skills if skill_name.lower() in s.lower()]
    if not matched:
        matched = [skill_name]

    mcqs = []
    for i in range(request.num_questions):
        concept = matched[i % len(matched)]
        mcq = mcq_generator.generate_mcqs_from_concept(
            concept,
            num_questions=1
        )[0]
        mcq["difficulty"] = request.difficulty
        mcq["concept"] = concept
        mcqs.append(mcq)

    quiz = Quiz(
        title=f"Skill Quiz: {skill_name}",
        questions=mcqs,
        difficulty=request.difficulty,
        category="skill_based",
        created_by=current_user.id
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return QuizResponse(
        id=quiz.id,
        title=quiz.title,
        questions=[QuestionResponse(**q) for q in mcqs],
        total_questions=len(mcqs),
        difficulty=request.difficulty,
        time_limit_minutes=len(mcqs) * 2
    )

@router.get("/skills")
async def list_available_skills():
    """List all O*NET skills available for quiz generation."""
    onet_skills = load_onet_skills()
    result = {}
    for category, skills in onet_skills.items():
        result[category] = sorted(set(skills))
    return result

@router.post("/generate-from-document")
async def generate_quiz_from_document(
    file: UploadFile = File(...),
    num_questions: int = 5,
    difficulty: str = "medium",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    processed = doc_processor.process_document(content, file.filename)
    
    mcqs = mcq_generator.generate_mcqs_from_text(
        processed["text"],
        num_questions=num_questions,
        difficulty=difficulty
    )
    
    quiz = Quiz(
        title=f"Quiz from {file.filename}",
        source_document=file.filename,
        questions=mcqs,
        difficulty=difficulty,
        category="document_based",
        created_by=current_user.id
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    return {
        "quiz_id": quiz.id,
        "title": quiz.title,
        "questions": mcqs,
        "document_info": {
            "filename": file.filename,
            "word_count": processed["word_count"],
            "file_type": processed["file_type"]
        }
    }

@router.post("/submit")
async def submit_quiz(
    request: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == request.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    evaluation = mcq_generator.evaluate_quiz(
        {"questions": quiz.questions},
        request.answers
    )
    
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=request.quiz_id,
        answers=request.answers,
        score=evaluation["score"],
        time_taken_seconds=request.time_taken_seconds
    )
    db.add(attempt)
    db.commit()
    
    return {
        "score": evaluation["score"],
        "grade": evaluation["grade"],
        "correct_count": evaluation["correct_count"],
        "total_questions": evaluation["total_questions"],
        "results": evaluation["results"]
    }

@router.get("/history")
async def get_quiz_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id
    ).order_by(QuizAttempt.completed_at.desc()).limit(20).all()
    
    return {
        "attempts": [
            {
                "id": a.id,
                "quiz_id": a.quiz_id,
                "score": a.score,
                "time_taken": a.time_taken_seconds,
                "completed_at": a.completed_at
            }
            for a in attempts
        ]
    }

@router.get("/{quiz_id}")
async def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return {
        "id": quiz.id,
        "title": quiz.title,
        "questions": quiz.questions,
        "difficulty": quiz.difficulty
    }

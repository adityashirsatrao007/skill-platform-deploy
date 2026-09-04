from typing import List, Dict, Optional
import random
import re
from .ml_loader import MLModels

class MCQGenerator:
    def __init__(self):
        self.ml = MLModels()
    
    def generate_mcqs_from_text(self, text: str, num_questions: int = 5, 
                                 difficulty: str = "medium") -> List[Dict]:
        """Generate MCQs from uploaded text content"""
        sentences = self._split_into_sentences(text)
        key_concepts = self._extract_key_concepts(text)
        
        mcqs = []
        
        for i in range(min(num_questions, len(sentences))):
            sentence = sentences[i % len(sentences)]
            
            question = self._generate_question_from_sentence(sentence)
            
            correct_answer = self._extract_answer_from_context(sentence, question)
            
            distractors = self._generate_distractors(correct_answer, key_concepts)
            
            options = [correct_answer] + distractors
            random.shuffle(options)
            
            correct_index = options.index(correct_answer)
            
            mcqs.append({
                "id": i + 1,
                "question": question,
                "options": options,
                "correct_answer": chr(65 + correct_index),
                "explanation": f"Based on the content: {sentence[:200]}...",
                "difficulty": difficulty,
                "concept": key_concepts[i % len(key_concepts)] if key_concepts else "General"
            })
        
        return mcqs
    
    def generate_mcqs_from_concept(self, concept: str, context: str = "",
                                    num_questions: int = 3) -> List[Dict]:
        """Generate MCQs for a specific concept"""
        prompt = f"Generate a multiple choice question about: {concept}"
        if context:
            prompt += f"\nContext: {context[:500]}"
        
        try:
            result = self.ml.text_generator(
                prompt,
                max_length=200,
                num_return_sequences=1
            )
            generated_text = result[0]['generated_text']
        except Exception:
            generated_text = f"What is {concept}?"
        
        mcqs = []
        for i in range(num_questions):
            question = f"What best describes {concept}?" if i == 0 else \
                      f"Which is true about {concept}?" if i == 1 else \
                      f"What is the purpose of {concept}?"
            
            options = [
                f"A key component of {concept}",
                f"Related to {concept} but not primary",
                f"Unrelated concept",
                f"Opposite of {concept}"
            ]
            
            mcqs.append({
                "id": i + 1,
                "question": question,
                "options": options,
                "correct_answer": "A",
                "explanation": f"{concept} is an important concept in this domain.",
                "difficulty": "medium",
                "concept": concept
            })
        
        return mcqs
    
    def generate_quiz(self, documents: List[str], title: str = "Generated Quiz",
                      num_questions: int = 10, difficulty: str = "medium") -> Dict:
        """Generate a complete quiz from multiple documents"""
        combined_text = " ".join(documents)
        
        all_mcqs = []
        for doc in documents:
            mcqs = self.generate_mcqs_from_text(doc, num_questions=3, difficulty=difficulty)
            all_mcqs.extend(mcqs)
        
        selected_mcqs = random.sample(all_mcqs, min(num_questions, len(all_mcqs)))
        
        for i, mcq in enumerate(selected_mcqs):
            mcq["id"] = i + 1
        
        return {
            "title": title,
            "questions": selected_mcqs,
            "total_questions": len(selected_mcqs),
            "difficulty": difficulty,
            "time_limit_minutes": len(selected_mcqs) * 2
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        doc = self.ml.nlp(text)
        return [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text using NLP"""
        doc = self.ml.nlp(text)
        
        concepts = []
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:
                concepts.append(chunk.text)
        
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "EVENT"]:
                concepts.append(ent.text)
        
        return list(set(concepts))[:10]
    
    def _generate_question_from_sentence(self, sentence: str) -> str:
        """Generate a question from a sentence"""
        prompt = f"Convert this statement into a question: {sentence}"
        
        try:
            result = self.ml.text_generator(
                prompt,
                max_length=100,
                num_return_sequences=1
            )
            return result[0]['generated_text']
        except Exception:
            words = sentence.split()
            if len(words) > 5:
                return f"Which of the following is related to {' '.join(words[3:7])}?"
            return f"What does this describe: {sentence[:50]}?"
    
    def _extract_answer_from_context(self, sentence: str, question: str) -> str:
        """Extract the correct answer from context"""
        doc = self.ml.nlp(sentence)
        
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        
        if noun_phrases:
            return noun_phrases[0]
        
        words = sentence.split()
        return " ".join(words[:5]) if len(words) >= 5 else sentence[:50]
    
    def _generate_distractors(self, correct_answer: str, 
                               all_concepts: List[str], 
                               num_distractors: int = 3) -> List[str]:
        """Generate plausible distractors"""
        distractors = []
        
        related_concepts = [c for c in all_concepts if c != correct_answer]
        random.shuffle(related_concepts)
        
        for concept in related_concepts[:num_distractors]:
            distractors.append(concept)
        
        generic_distractors = [
            "None of the above",
            "All of the above",
            "Cannot be determined",
            "Not applicable"
        ]
        
        while len(distractors) < num_distractors:
            distractors.append(random.choice(generic_distractors))
        
        return distractors[:num_distractors]
    
    def evaluate_quiz(self, quiz: Dict, user_answers: Dict) -> Dict:
        """Evaluate quiz answers and return results"""
        questions = quiz["questions"]
        correct_count = 0
        results = []
        
        for q in questions:
            q_id = str(q["id"])
            user_answer = user_answers.get(q_id)
            is_correct = user_answer == q["correct_answer"]
            
            if is_correct:
                correct_count += 1
            
            results.append({
                "question_id": q_id,
                "question": q["question"],
                "user_answer": user_answer,
                "correct_answer": q["correct_answer"],
                "is_correct": is_correct,
                "explanation": q.get("explanation", "")
            })
        
        total = len(questions)
        score = (correct_count / total * 100) if total > 0 else 0
        
        return {
            "score": round(score, 2),
            "correct_count": correct_count,
            "total_questions": total,
            "results": results,
            "grade": self._calculate_grade(score)
        }
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate grade based on score"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InterviewQuestion(BaseModel):
    """Represents an interview question with metadata."""
    
    question_id: str = Field(..., description="Unique identifier for the question")
    question_text: str = Field(..., description="The actual question text")
    category: str = Field(..., description="Category of the question (e.g., technical, behavioral)")
    difficulty: str = Field(default="medium", description="Difficulty level: easy, medium, hard")


class InterviewSession(BaseModel):
    """Represents an interview session with state management."""
    
    session_id: str = Field(..., description="Unique session identifier")
    candidate_name: str = Field(..., description="Name of the candidate")
    position: str = Field(..., description="Position being interviewed for")
    start_time: datetime = Field(default_factory=datetime.now)
    current_question_index: int = Field(default=0)
    questions: List[InterviewQuestion] = Field(default_factory=list)
    answers: List[Dict[str, Any]] = Field(default_factory=list)
    session_status: str = Field(default="active", description="active, paused, completed")


class InterviewAgent:
    """An AI agent that conducts interviews by asking questions and managing the interview flow."""
    
    def __init__(self, session_id: str, candidate_name: str, position: str, questions_file: str = "questions.json"):
        """Initialize the interview agent with session details.
        
        Args:
            session_id: Unique identifier for the interview session
            candidate_name: Name of the candidate being interviewed
            position: Position the candidate is applying for
            questions_file: Path to the JSON file containing questions
        """
        self.session = InterviewSession(
            session_id=session_id,
            candidate_name=candidate_name,
            position=position
        )
        self.logger = logging.getLogger(__name__)
        self.questions_file = questions_file
        self._load_questions()
    
    def _load_questions(self) -> None:
        """Load questions from the JSON file."""
        try:
            # Get the path to the questions file relative to this module
            current_dir = Path(__file__).parent
            questions_path = current_dir / self.questions_file
            
            if not questions_path.exists():
                self.logger.error(f"Questions file not found: {questions_path}")
                return
            
            with open(questions_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            questions_data = data.get('questions', [])
            for q_data in questions_data:
                question = InterviewQuestion(**q_data)
                self.session.questions.append(question)
            
            self.logger.info(f"Loaded {len(self.session.questions)} questions from {questions_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading questions from {self.questions_file}: {str(e)}")
    
    def add_questions(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add questions to the interview session.
        
        Args:
            questions: List of question dictionaries with required fields
            
        Returns:
            Dictionary with status and count of added questions
        """
        try:
            added_count = 0
            for q_data in questions:
                question = InterviewQuestion(**q_data)
                self.session.questions.append(question)
                added_count += 1
                
            self.logger.info(f"Added {added_count} questions to session {self.session.session_id}")
            return {
                "status": "success",
                "message": f"Added {added_count} questions to the interview",
                "total_questions": len(self.session.questions)
            }
        except Exception as e:
            self.logger.error(f"Error adding questions: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to add questions: {str(e)}"
            }
    
    def get_next_question(self) -> Dict[str, Any]:
        """Get the next question in the interview sequence.
        
        Returns:
            Dictionary containing the next question or session completion status
        """
        if self.session.current_question_index >= len(self.session.questions):
            return {
                "status": "completed",
                "message": "Interview completed - no more questions",
                "session_summary": self._get_session_summary()
            }
        
        current_question = self.session.questions[self.session.current_question_index]
        
        return {
            "status": "success",
            "question": {
                "id": current_question.question_id,
                "text": current_question.question_text,
                "category": current_question.category,
                "difficulty": current_question.difficulty,
                "question_number": self.session.current_question_index + 1,
                "total_questions": len(self.session.questions)
            },
            "session_info": {
                "candidate_name": self.session.candidate_name,
                "position": self.session.position,
                "elapsed_time": self._get_elapsed_time()
            }
        }
    
    def record_answer(self, question_id: str, answer_text: str, notes: str = "") -> Dict[str, Any]:
        """Record the candidate's answer to a question.
        
        Args:
            question_id: ID of the question being answered
            answer_text: The candidate's answer
            notes: Optional notes about the answer
            
        Returns:
            Dictionary with recording status and next steps
        """
        try:
            # Find the current question
            current_question = None
            for q in self.session.questions:
                if q.question_id == question_id:
                    current_question = q
                    break
            
            if not current_question:
                return {
                    "status": "error",
                    "message": f"Question with ID {question_id} not found"
                }
            
            # Record the answer
            answer_record = {
                "question_id": question_id,
                "answer_text": answer_text,
                "notes": notes,
                "timestamp": datetime.now().isoformat(),
                "question_category": current_question.category,
                "question_difficulty": current_question.difficulty
            }
            
            self.session.answers.append(answer_record)
            self.session.current_question_index += 1
            
            self.logger.info(f"Recorded answer for question {question_id} in session {self.session.session_id}")
            
            # Check if interview is complete
            if self.session.current_question_index >= len(self.session.questions):
                self.session.session_status = "completed"
                return {
                    "status": "completed",
                    "message": "Interview completed successfully",
                    "session_summary": self._get_session_summary()
                }
            
            return {
                "status": "success",
                "message": "Answer recorded successfully",
                "next_question": self.get_next_question()
            }
            
        except Exception as e:
            self.logger.error(f"Error recording answer: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to record answer: {str(e)}"
            }

def ask_next_interview_question_sync(session_id: str) -> Dict[str, Any]:
    """Get the next question in the interview sequence.
    
    Args:
        session_id: ID of the interview session
        
    Returns:
        Dictionary with the next question or completion status
    """
    try:
        # Import the global session storage from agent.py
        from ..agent import interview_sessions
        
        if session_id not in interview_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found. Please start with job analysis first."
            }
        
        session = interview_sessions[session_id]
        questions = session.get("questions", [])
        current_index = session.get("current_question_index", 0)
        
        if current_index >= len(questions):
            return {
                "success": True,
                "status": "completed",
                "message": "Interview completed - no more questions",
                "session_summary": {
                    "total_questions": len(questions),
                    "total_answers": len(session.get("answers", [])),
                    "position": session.get("vacancy_info", {}).get("job_title", "Unknown")
                }
            }
        
        current_question = questions[current_index]
        
        return {
            "success": True,
            "status": "success",
            "question": {
                "id": f"q{current_index + 1}",
                "text": current_question.get("question", ""),
                "type": current_question.get("question_type", "general"),
                "difficulty": current_question.get("difficulty_level", "medium"),
                "skills_assessed": current_question.get("skills_assessed", []),
                "question_number": current_index + 1,
                "total_questions": len(questions)
            },
            "session_info": {
                "session_id": session_id,
                "position": session.get("vacancy_info", {}).get("job_title", "Unknown Position"),
                "current_question": current_index + 1,
                "total_questions": len(questions)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get next question: {str(e)}"
        }


def record_interview_answer_sync(session_id: str, question_id: str, answer_text: str, notes: str = "") -> Dict[str, Any]:
    """Record a candidate's answer to an interview question.
    
    Args:
        session_id: ID of the interview session
        question_id: ID of the question being answered
        answer_text: The candidate's answer
        notes: Optional notes about the answer
        
    Returns:
        Dictionary with recording status
    """
    try:
        # Import the global session storage from agent.py
        from ..agent import interview_sessions
        
        if session_id not in interview_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        session = interview_sessions[session_id]
        questions = session.get("questions", [])
        current_index = session.get("current_question_index", 0)
        
        if current_index >= len(questions):
            return {
                "success": False,
                "error": "No more questions to answer"
            }
        
        # Record the answer
        if "answers" not in session:
            session["answers"] = []
        
        answer_record = {
            "question_id": question_id,
            "question_text": questions[current_index].get("question", ""),
            "answer_text": answer_text,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "question_type": questions[current_index].get("question_type", "general"),
            "difficulty_level": questions[current_index].get("difficulty_level", "medium"),
            "skills_assessed": questions[current_index].get("skills_assessed", [])
        }
        
        session["answers"].append(answer_record)
        session["current_question_index"] = current_index + 1
        
        # Check if interview is complete
        if session["current_question_index"] >= len(questions):
            session["status"] = "completed"
            return {
                "success": True,
                "status": "completed",
                "message": "Interview completed successfully",
                "session_summary": {
                    "total_questions": len(questions),
                    "total_answers": len(session["answers"]),
                    "position": session.get("vacancy_info", {}).get("job_title", "Unknown")
                }
            }
        
        return {
            "success": True,
            "status": "success",
            "message": "Answer recorded successfully",
            "next_question": ask_next_interview_question_sync(session_id)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to record answer: {str(e)}"
        }

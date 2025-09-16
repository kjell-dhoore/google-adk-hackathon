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
    
    def pause_interview(self) -> Dict[str, Any]:
        """Pause the interview session.
        
        Returns:
            Dictionary with pause status
        """
        self.session.session_status = "paused"
        self.logger.info(f"Interview session {self.session.session_id} paused")
        
        return {
            "status": "success",
            "message": "Interview paused",
            "session_info": {
                "status": self.session.session_status,
                "current_question": self.session.current_question_index + 1,
                "total_questions": len(self.session.questions),
                "elapsed_time": self._get_elapsed_time()
            }
        }
    
    def resume_interview(self) -> Dict[str, Any]:
        """Resume the interview session.
        
        Returns:
            Dictionary with resume status and next question
        """
        if self.session.session_status != "paused":
            return {
                "status": "error",
                "message": "Interview is not paused"
            }
        
        self.session.session_status = "active"
        self.logger.info(f"Interview session {self.session.session_id} resumed")
        
        return {
            "status": "success",
            "message": "Interview resumed",
            "next_question": self.get_next_question()
        }
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status and progress.
        
        Returns:
            Dictionary with session status information
        """
        return {
            "session_id": self.session.session_id,
            "candidate_name": self.session.candidate_name,
            "position": self.session.position,
            "status": self.session.session_status,
            "progress": {
                "current_question": self.session.current_question_index + 1,
                "total_questions": len(self.session.questions),
                "completed_questions": len(self.session.answers),
                "percentage_complete": (len(self.session.answers) / len(self.session.questions) * 100) if self.session.questions else 0
            },
            "elapsed_time": self._get_elapsed_time(),
            "start_time": self.session.start_time.isoformat()
        }
    
    def _get_elapsed_time(self) -> str:
        """Calculate and format elapsed time since session start."""
        elapsed = datetime.now() - self.session.start_time
        total_seconds = int(elapsed.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _get_session_summary(self) -> Dict[str, Any]:
        """Generate a summary of the completed interview session."""
        if not self.session.answers:
            return {"message": "No answers recorded yet"}
        
        categories = {}
        
        for answer in self.session.answers:
            category = answer["question_category"]
            if category not in categories:
                categories[category] = {"count": 0}
            categories[category]["count"] += 1
        
        return {
            "total_questions_asked": len(self.session.answers),
            "categories_covered": categories,
            "completion_time": datetime.now().isoformat()
        }


# Tool functions for integration with the Gemini Live API

def start_interview_session(session_id: str, candidate_name: str, position: str) -> Dict[str, Any]:
    """Start a new interview session.
    
    Args:
        session_id: Unique identifier for the session
        candidate_name: Name of the candidate
        position: Position being interviewed for
        
    Returns:
        Dictionary with session initialization status
    """
    try:
        agent = InterviewAgent(session_id, candidate_name, position)
        # Store the agent instance (in a real implementation, you'd use a proper storage mechanism)
        return {
            "status": "success",
            "message": f"Interview session started for {candidate_name}",
            "session_id": session_id,
            "position": position
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to start interview session: {str(e)}"
        }


def add_interview_questions(session_id: str, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Add questions to an interview session.
    
    Note: Questions are now loaded automatically from the JSON file.
    This function is kept for compatibility but questions are pre-loaded.
    
    Args:
        session_id: ID of the interview session
        questions: List of question dictionaries (ignored, questions loaded from JSON)
        
    Returns:
        Dictionary with question addition status
    """
    try:
        agent = InterviewAgent(session_id, "Demo Candidate", "Demo Position")
        return {
            "status": "success",
            "message": f"Questions loaded from JSON file. Total questions: {len(agent.session.questions)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to load questions: {str(e)}"
        }


def get_next_interview_question(session_id: str) -> Dict[str, Any]:
    """Get the next question in the interview sequence.
    
    Args:
        session_id: ID of the interview session
        
    Returns:
        Dictionary with the next question or completion status
    """
    try:
        # In a real implementation, you'd retrieve the agent instance from storage
        agent = InterviewAgent(session_id, "Demo Candidate", "Demo Position")
        return agent.get_next_question()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get next question: {str(e)}"
        }


def record_interview_answer(session_id: str, question_id: str, answer_text: str, notes: str = "") -> Dict[str, Any]:
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
        # In a real implementation, you'd retrieve the agent instance from storage
        agent = InterviewAgent(session_id, "Demo Candidate", "Demo Position")
        return agent.record_answer(question_id, answer_text, notes)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to record answer: {str(e)}"
        }


def get_interview_status(session_id: str) -> Dict[str, Any]:
    """Get the current status of an interview session.
    
    Args:
        session_id: ID of the interview session
        
    Returns:
        Dictionary with session status information
    """
    try:
        # In a real implementation, you'd retrieve the agent instance from storage
        agent = InterviewAgent(session_id, "Demo Candidate", "Demo Position")
        return agent.get_session_status()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get session status: {str(e)}"
        }

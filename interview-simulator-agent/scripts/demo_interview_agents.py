#!/usr/bin/env python3
"""
Demo script showing how to use both VacancyAgent and InterviewQuestionAgent together.

This script demonstrates the complete workflow:
1. Analyze a job vacancy to extract structured information
2. Generate interview questions based on that information
"""

import sys
import os
import json
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "app"))

from agents.vacancy_agent import analyze_job_vacancy_sync
from agents.interview_question_agent import generate_interview_questions_from_vacancy_sync


def demo_interview_workflow():
    """Demonstrate the complete interview preparation workflow."""
    
    # Sample job description
    job_description = """
    Senior Software Engineer - Full Stack Development
    
    Company: TechCorp Solutions
    Location: San Francisco, CA (Remote OK)
    Employment Type: Full-time
    
    We are seeking a Senior Software Engineer to join our dynamic engineering team. 
    You will be responsible for developing and maintaining our web applications and APIs.
    
    Key Responsibilities:
    - Design and develop scalable web applications using React, Node.js, and Python
    - Build and maintain RESTful APIs and microservices
    - Collaborate with cross-functional teams including product, design, and QA
    - Mentor junior developers and conduct code reviews
    - Implement CI/CD pipelines and DevOps best practices
    - Optimize application performance and ensure high availability
    
    Required Skills:
    - 5+ years of software development experience
    - Strong proficiency in JavaScript, Python, and SQL
    - Experience with React, Node.js, and Django/FastAPI
    - Knowledge of cloud platforms (AWS, GCP, or Azure)
    - Experience with Docker, Kubernetes, and containerization
    - Strong understanding of software architecture and design patterns
    - Excellent problem-solving and communication skills
    
    Preferred Skills:
    - Experience with TypeScript and GraphQL
    - Knowledge of machine learning and data science
    - Experience with monitoring and observability tools
    - Previous experience in fintech or e-commerce
    
    Education Requirements:
    - Bachelor's degree in Computer Science or related field
    
    Benefits:
    - Competitive salary and equity
    - Health, dental, and vision insurance
    - Flexible work arrangements
    - Professional development budget
    - 401(k) matching
    
    We value innovation, collaboration, and continuous learning. Join us in building 
    the next generation of financial technology solutions!
    """
    
    print("🚀 Starting Interview Preparation Workflow")
    print("=" * 50)
    
    # Step 1: Analyze the job vacancy
    print("\n📋 Step 1: Analyzing Job Vacancy...")
    vacancy_result = analyze_job_vacancy_sync(job_description)
    
    if not vacancy_result.get("success"):
        print(f"❌ Vacancy analysis failed: {vacancy_result.get('error')}")
        return
    
    print("✅ Vacancy analysis completed!")
    
    # Display vacancy summary
    summary = vacancy_result.get("summary", {})
    print(f"\n📊 Job Summary:")
    print(f"   Title: {summary.get('title')}")
    print(f"   Company: {summary.get('company')}")
    print(f"   Seniority: {summary.get('seniority')}")
    print(f"   Key Skills: {', '.join(summary.get('key_skills', []))}")
    print(f"   Technologies: {', '.join(summary.get('technologies', []))}")
    
    # Step 2: Generate interview questions
    print("\n❓ Step 2: Generating Interview Questions...")
    questions_result = generate_interview_questions_from_vacancy_sync(vacancy_result)
    
    if not questions_result.get("success"):
        print(f"❌ Question generation failed: {questions_result.get('error')}")
        return
    
    print("✅ Interview questions generated!")
    
    # Display questions
    questions = questions_result.get("questions", [])
    interview_focus = questions_result.get("interview_focus", {})
    evaluation_criteria = questions_result.get("evaluation_criteria", [])
    
    print(f"\n🎯 Interview Focus Areas:")
    for focus_type, description in interview_focus.items():
        print(f"   {focus_type.replace('_', ' ').title()}: {description}")
    
    print(f"\n📝 Evaluation Criteria:")
    for i, criteria in enumerate(evaluation_criteria, 1):
        print(f"   {i}. {criteria}")
    
    print(f"\n❓ Generated Interview Questions:")
    print("-" * 50)
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. {question.get('question')}")
        print(f"   Type: {question.get('question_type').title()}")
        print(f"   Difficulty: {question.get('difficulty_level').title()}")
        print(f"   Skills Assessed: {', '.join(question.get('skills_assessed', []))}")
        print(f"   Expected Focus: {question.get('expected_answer_focus')}")
        
        follow_ups = question.get('follow_up_suggestions', [])
        if follow_ups:
            print(f"   Follow-up Questions:")
            for j, follow_up in enumerate(follow_ups, 1):
                print(f"     {j}. {follow_up}")
    
    print("\n🎉 Interview preparation workflow completed successfully!")
    
    # Optional: Save results to file
    save_results = input("\n💾 Save results to file? (y/n): ").lower().strip()
    if save_results == 'y':
        results = {
            "vacancy_analysis": vacancy_result,
            "interview_questions": questions_result,
            "workflow_summary": {
                "job_title": summary.get('title'),
                "company": summary.get('company'),
                "total_questions": len(questions),
                "question_types": [q.get('question_type') for q in questions]
            }
        }
        
        filename = f"interview_prep_{summary.get('title', 'job').replace(' ', '_').lower()}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✅ Results saved to {filename}")


if __name__ == "__main__":
    try:
        demo_interview_workflow()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


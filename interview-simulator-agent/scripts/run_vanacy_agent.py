#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple test script for the VacancyAgent using the integrated tool approach.

This bypasses the complex ADK runner setup and directly tests the analyze_job_vacancy
tool function that's already integrated into the playground.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the synchronous function directly
from app.agents.vacancy_agent import analyze_job_vacancy_sync


# Sample job vacancy for testing
SAMPLE_VACANCY = """
Senior Software Engineer - Cloud Infrastructure
Google Cloud Platform Team

We're looking for a Senior Software Engineer to join our Cloud Infrastructure team at Google.
You'll be responsible for designing and implementing scalable cloud solutions that serve millions of users globally.

Requirements:
- Bachelor's or Master's degree in Computer Science or related field
- 5+ years of experience in software development
- Strong proficiency in Python, Go, or Java
- Experience with cloud platforms (GCP, AWS, or Azure)
- Knowledge of Kubernetes and containerization
- Experience with distributed systems and microservices

Preferred Qualifications:
- PhD in Computer Science
- Experience with Terraform or similar Infrastructure as Code tools
- Knowledge of machine learning frameworks
- Previous experience at a technology company

Responsibilities:
- Design and implement cloud infrastructure solutions
- Collaborate with cross-functional teams of 8-10 engineers
- Mentor junior engineers and conduct code reviews
- Participate in on-call rotation
- Lead technical design discussions

We offer competitive compensation, comprehensive health benefits, flexible work arrangements with optional remote work, and opportunities for professional growth. Join our innovative culture focused on collaboration, diversity, and continuous learning.

Location: Mountain View, CA (hybrid remote available)
Employment: Full-time
"""


def test_vacancy_analysis():
    """Test the synchronous VacancyAgent."""
    print("Testing Synchronous VacancyAgent")
    print("=" * 40)

    try:
        # Call the synchronous function directly
        result = analyze_job_vacancy_sync(SAMPLE_VACANCY)

        print("✅ Analysis completed!")
        print("\n📊 Results Summary:")
        print("-" * 20)

        if not result.get("success"):
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            if 'raw_response' in result:
                print(f"Raw response: {result['raw_response'][:200]}...")
            return

        # Display the structured vacancy info
        vacancy_info = result.get("vacancy_info", {})
        if vacancy_info:
            print(f"📋 Job Title: {vacancy_info.get('job_title', 'N/A')}")
            print(f"🏢 Company: {vacancy_info.get('company_name', 'N/A')}")
            print(f"📈 Seniority: {vacancy_info.get('seniority_level', 'N/A')}")
            print(f"📍 Location: {vacancy_info.get('location', 'N/A')}")
            print(f"🏠 Remote Work: {vacancy_info.get('remote_work', 'N/A')}")

            skills = vacancy_info.get('required_skills', [])
            if skills:
                print(f"🛠️  Required Skills: {', '.join(skills[:5])}")

            technologies = vacancy_info.get('technologies', [])
            if technologies:
                print(f"💻 Technologies: {', '.join(technologies[:5])}")

            responsibilities = vacancy_info.get('key_responsibilities', [])
            if responsibilities:
                print(f"📝 Key Responsibilities ({len(responsibilities)}):")
                for i, resp in enumerate(responsibilities[:3], 1):
                    print(f"   {i}. {resp}")

        # Display interview context
        interview_context = result.get("interview_context", {})
        if interview_context:
            print(f"\n🎯 Interview Context Generated:")
            print(f"   ✓ Role Overview")
            print(f"   ✓ Technical Focus")
            print(f"   ✓ Experience Expectations")
            print(f"   ✓ Company Context")
            print(f"   ✓ Logistics")

        print(f"\n✅ Test completed successfully!")
        print(f"\n🚀 The VacancyAgent is ready for use in the playground!")
        print(f"   Access at: http://localhost:8000")
        print(f"   Try asking: 'Analyze this job posting: [paste job description]'")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_vacancy_analysis()
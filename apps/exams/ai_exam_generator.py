"""
AI-Powered Exam Generator
Uses Gemini AI to generate custom exams on any topic
"""
import json
import urllib.request
import urllib.error
from django.conf import settings
from .models import Exam, Question, QuestionOption, ExamCategory
from apps.students.models import Course
from django.utils import timezone
from datetime import timedelta
import uuid


class AIExamGenerator:
    """Generate exams using Gemini AI"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        # Use the same models that work in the chatbot
        self.models = [
            'gemini-flash-lite-latest',
            'gemini-flash-latest',
            'gemini-2.5-flash-lite',
            'gemini-2.0-flash-lite'
        ]
    
    def generate_exam(self, topic, course_code, num_questions=10, difficulty='medium', 
                     question_types=['multiple_choice'], duration_minutes=30, user=None):
        """
        Generate a complete exam using AI
        
        Args:
            topic: The subject/topic for the exam
            course_code: Course code (e.g., CS101)
            num_questions: Number of questions to generate
            difficulty: easy, medium, or hard
            question_types: List of question types to include
            duration_minutes: Exam duration
            user: User creating the exam
        
        Returns:
            Exam object with generated questions
        """
        
        # Build the prompt for AI
        prompt = self._build_generation_prompt(
            topic, num_questions, difficulty, question_types
        )
        
        try:
            # Generate questions using AI
            response_text = self._call_gemini_api(prompt)
            
            if not response_text:
                raise ValueError("AI failed to generate response")
            
            # Parse the AI response
            questions_data = self._parse_ai_response(response_text)
            
            if not questions_data:
                raise ValueError("AI failed to generate valid questions")
            
            # Create the exam in database
            exam = self._create_exam_from_data(
                topic, course_code, questions_data, 
                difficulty, duration_minutes, user
            )
            
            return exam
            
        except Exception as e:
            print(f"AI Exam Generation Error: {e}")
            raise
    
    def _build_generation_prompt(self, topic, num_questions, difficulty, question_types):
        """Build the prompt for AI exam generation"""
        
        types_str = ", ".join(question_types)
        
        prompt = f"""You are an expert exam creator. Generate {num_questions} high-quality exam questions about: {topic}

REQUIREMENTS:
- Difficulty level: {difficulty}
- Question types: {types_str}
- Questions should be clear, unambiguous, and academically rigorous
- For multiple choice: provide 4 options with only ONE correct answer
- For true/false: provide a clear statement
- For fill_blank: provide a statement with _____ where the answer goes, and provide the correct answer in options
- Ensure questions test understanding, not just memorization

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "question_text": "What is...",
      "question_type": "multiple_choice",
      "marks": 2,
      "options": [
        {{"text": "Option A", "is_correct": false}},
        {{"text": "Option B", "is_correct": true}},
        {{"text": "Option C", "is_correct": false}},
        {{"text": "Option D", "is_correct": false}}
      ]
    }},
    {{
      "question_text": "True or False: ...",
      "question_type": "true_false",
      "marks": 1,
      "options": [
        {{"text": "True", "is_correct": true}},
        {{"text": "False", "is_correct": false}}
      ]
    }},
    {{
      "question_text": "The capital of France is _____.",
      "question_type": "fill_blank",
      "marks": 1,
      "expected_answer": "Paris"
    }}
  ]
}}

Generate exactly {num_questions} questions. Return ONLY valid JSON, no markdown formatting."""
        
        return prompt
    
    def _call_gemini_api(self, prompt):
        """Call Gemini API using urllib (same approach as chatbot)"""
        if not self.api_key:
            print("❌ No Gemini API key found")
            return None
        
        # Build request payload with higher token limit
        payload = json.dumps({
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8192,  # Increased from 4096
            }
        }).encode('utf-8')
        
        # Try models in order
        for model in self.models:
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}'
            req = urllib.request.Request(
                url, 
                data=payload, 
                headers={'Content-Type': 'application/json'}, 
                method='POST'
            )
            
            try:
                print(f"🔄 Trying Gemini model: {model}")
                with urllib.request.urlopen(req, timeout=60) as resp:  # Increased timeout
                    data = json.loads(resp.read().decode('utf-8'))
                    
                    if 'candidates' in data and len(data['candidates']) > 0:
                        content = data['candidates'][0].get('content', {})
                        parts = content.get('parts', [])
                        if parts and 'text' in parts[0]:
                            print(f"✅ Successfully used model: {model}")
                            return parts[0]['text']
                    
                    print(f"⚠️ Model {model} returned no content")
                    
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8') if e.fp else ''
                print(f"⚠️ Model {model} failed: {e.code} - {error_body[:200]}")
                continue
            except Exception as e:
                print(f"⚠️ Model {model} error: {e}")
                continue
        
        print("❌ All models failed")
        return None
    
    def _parse_ai_response(self, response_text):
        """Parse AI response and extract questions"""
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```'):
                # Remove ```json or ``` at start
                response_text = response_text.split('\n', 1)[1]
            if response_text.endswith('```'):
                # Remove ``` at end
                response_text = response_text.rsplit('\n', 1)[0]
            
            # Try to parse JSON
            try:
                data = json.loads(response_text)
                return data.get('questions', [])
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                print(f"Response length: {len(response_text)} chars")
                
                # Try to fix incomplete JSON by finding the last complete question
                # Look for the last complete question object
                last_complete = response_text.rfind('}')
                if last_complete > 0:
                    # Try to close the questions array and main object
                    truncated = response_text[:last_complete + 1]
                    
                    # Count opening and closing brackets
                    open_brackets = truncated.count('[')
                    close_brackets = truncated.count(']')
                    open_braces = truncated.count('{')
                    close_braces = truncated.count('}')
                    
                    # Add missing closing brackets
                    if close_brackets < open_brackets:
                        truncated += ']' * (open_brackets - close_brackets)
                    if close_braces < open_braces:
                        truncated += '}' * (open_braces - close_braces)
                    
                    print(f"🔧 Attempting to fix truncated JSON...")
                    try:
                        data = json.loads(truncated)
                        questions = data.get('questions', [])
                        print(f"✅ Recovered {len(questions)} questions from truncated response")
                        return questions
                    except:
                        pass
                
                print(f"Response preview: {response_text[:500]}")
                return None
                
        except Exception as e:
            print(f"Parse Error: {e}")
            return None
    
    def _create_exam_from_data(self, topic, course_code, questions_data, 
                               difficulty, duration_minutes, user):
        """Create exam and questions in database from AI-generated data"""
        
        # Get or create course
        try:
            course = Course.objects.get(code=course_code)
        except Course.DoesNotExist:
            # Create a generic course for AI-generated exams
            from apps.students.models import Department
            dept = Department.objects.first()
            course = Course.objects.create(
                code=course_code,
                name=f"AI Generated - {topic}",
                department=dept,
                credit_hours=3,
                level=100,
                semester=1
            )
        
        # Get or create AI category
        category, _ = ExamCategory.objects.get_or_create(
            name="AI Generated",
            defaults={'description': 'Exams generated by AI on demand'}
        )
        
        # Calculate total marks
        total_marks = sum(q.get('marks', 1) for q in questions_data)
        
        # Create exam
        exam = Exam.objects.create(
            title=f"AI Exam: {topic}",
            course=course,
            category=category,
            exam_type='practice',
            difficulty=difficulty,
            description=f"AI-generated exam on {topic}",
            instructions="Answer all questions to the best of your ability.",
            duration_minutes=duration_minutes,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(days=30),
            total_marks=total_marks,
            pass_mark=int(total_marks * 0.5),
            shuffle_questions=True,
            shuffle_options=True,
            show_results_immediately=True,
            allow_review=True,
            max_attempts=3,
            created_by=user,
            is_active=True,
            is_published=True
        )
        
        # Create questions
        for idx, q_data in enumerate(questions_data, 1):
            question = Question.objects.create(
                exam=exam,
                question_text=q_data['question_text'],
                question_type=q_data.get('question_type', 'multiple_choice'),
                marks=q_data.get('marks', 1),
                order=idx,
                expected_answer=q_data.get('expected_answer', '')  # For fill_blank questions
            )
            
            # Create options (for multiple_choice and true_false)
            for opt_idx, opt_data in enumerate(q_data.get('options', []), 1):
                QuestionOption.objects.create(
                    question=question,
                    option_text=opt_data['text'],
                    is_correct=opt_data['is_correct'],
                    order=opt_idx
                )
        
        return exam
    
    def regenerate_question(self, question_id, topic):
        """Regenerate a single question using AI"""
        prompt = f"""Generate ONE high-quality exam question about: {topic}

OUTPUT FORMAT (JSON):
{{
  "question_text": "What is...",
  "question_type": "multiple_choice",
  "marks": 2,
  "options": [
    {{"text": "Option A", "is_correct": false}},
    {{"text": "Option B", "is_correct": true}},
    {{"text": "Option C", "is_correct": false}},
    {{"text": "Option D", "is_correct": false}}
  ]
}}

Return ONLY valid JSON."""
        
        try:
            response_text = self._call_gemini_api(prompt)
            if response_text:
                data = self._parse_ai_response(response_text)
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"Question regeneration error: {e}")
            return None

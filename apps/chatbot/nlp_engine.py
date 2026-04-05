"""
KAAF AI - Intelligent Campus Assistant
Full AI-powered engine with OpenAI integration, role-aware system prompt,
multilingual support, and comprehensive intent handling.
"""
import json
import random
import re
import os
from pathlib import Path
from django.conf import settings


# ─── University Knowledge Base ────────────────────────────────────────────────

UNIVERSITY_KB = {
    "name": "KAAF University",
    "faculties": [
        {"name": "Faculty of Business and Management Studies", "code": "FBMS",
         "departments": ["Accounting", "Business Administration", "Marketing", "Finance",
                         "Human Resource Management", "Logistics and Supply Chain Management", "Entrepreneurship"]},
        {"name": "Faculty of Information Technology", "code": "FIT",
         "departments": ["Computer Science", "Information Technology", "Software Engineering",
                         "Cybersecurity", "Data Science and Analytics", "Network Engineering"]},
        {"name": "Faculty of Health Sciences", "code": "FHS",
         "departments": ["Public Health", "Nursing", "Medical Laboratory Science",
                         "Pharmacy", "Environmental Health", "Community Health"]},
        {"name": "Faculty of Education", "code": "FED",
         "departments": ["Early Childhood Education", "Basic Education", "Educational Administration",
                         "Guidance and Counseling", "Special Education"]},
        {"name": "Faculty of Social Sciences and Humanities", "code": "FSSH",
         "departments": ["Communication Studies", "Sociology", "Political Science",
                         "Psychology", "Languages and Literature", "History"]},
        {"name": "Faculty of Law", "code": "FLAW",
         "departments": ["General Law", "Corporate and Commercial Law", "International Law", "Criminal Law"]},
        {"name": "Postgraduate School", "code": "PGS",
         "departments": ["MBA", "MSc programmes", "PhD programmes", "Executive Education"]},
    ],
    "admin_departments": [
        "Office of the Registrar", "Bursary and Finance", "Human Resources",
        "IT Services", "Library and Information Services", "Student Affairs",
        "Health Services", "Security Services", "Facilities and Maintenance",
        "Public Relations and Communications", "Admissions Office",
        "Academic Affairs", "Research and Innovation", "International Relations",
        "Career Services and Internship", "Alumni Relations",
    ],
    "contacts": {
        "admissions": "admissions@kaaf.edu.gh",
        "scholarships": "scholarships@kaaf.edu.gh",
        "finance": "finance@kaaf.edu.gh",
        "registrar": "registrar@kaaf.edu.gh",
        "it_support": "itsupport@kaaf.edu.gh",
        "health": "health@kaaf.edu.gh",
        "counseling": "counseling@kaaf.edu.gh",
        "career": "careers@kaaf.edu.gh",
        "library": "library@kaaf.edu.gh",
        "general": "info@kaaf.edu.gh",
    },
    "payment_methods": ["MTN Mobile Money", "Vodafone Cash", "AirtelTigo Money", "Paystack", "Bank Transfer"],
    "crisis_lines": ["Mental Health Authority Ghana: 0800-111-222", "Campus Counselor: 0302-XXX-XXX"],
}

ESCALATION_MATRIX = {
    "grade dispute": "Course Lecturer → HOD → Academic Affairs Office",
    "fee payment": "Bursary Staff → Finance Director (finance@kaaf.edu.gh)",
    "mental health": "Campus Counselor → Health Center (counseling@kaaf.edu.gh)",
    "harassment": "Student Affairs Office → Admin",
    "technical": "IT Support (itsupport@kaaf.edu.gh)",
    "admission": "Admissions Office (admissions@kaaf.edu.gh)",
    "transcript": "Registrar Office (registrar@kaaf.edu.gh)",
    "payroll": "HR Department",
}


# ─── System Prompt Builder ─────────────────────────────────────────────────────

def build_system_prompt(user):
    """Build a rich, role-aware system prompt for the AI."""
    role = user.role
    name = user.get_full_name()
    lang = getattr(user, 'preferred_language', 'English')

    base = f"""You are KAAF AI, the official intelligent assistant of KAAF University, Ghana.

IDENTITY:
- You are KAAF AI — friendly, accurate, and always helpful
- Institution: KAAF University, Ghana
- Respond in: {lang}. If the user writes in Twi, Ga, Hausa, or Pidgin, match their language.

STRICT RULES — follow these exactly:
1. Address the user by first name: {user.first_name}
2. NEVER fabricate academic data (grades, GPA, fees, exam dates). If real data is provided in [LIVE DATA], use it. If not, say you don't have it and direct them to the right office.
3. NEVER share another user's data
4. For questions about OTHER universities (UG, KNUST, UCC, etc.) — answer them accurately using your general knowledge. Do NOT pretend they are asking about KAAF.
5. For general knowledge questions (science, history, math, etc.) — answer them accurately and helpfully. You are a full AI assistant, not just a campus bot.
6. For mental health distress — always include: {', '.join(UNIVERSITY_KB['crisis_lines'])}
7. Keep responses concise — under 250 words unless the user asks for detail
8. Use markdown: **bold** for key info, bullet points for lists, emojis sparingly
9. End with one short follow-up suggestion when relevant

KAAF UNIVERSITY FACTS:
- Location: Ghana
- Faculties: {', '.join(f['code'] + ' (' + f['name'] + ')' for f in UNIVERSITY_KB['faculties'])}
- Fee payment: {', '.join(UNIVERSITY_KB['payment_methods'])}
- Key contacts: Finance: {UNIVERSITY_KB['contacts']['finance']} | Admissions: {UNIVERSITY_KB['contacts']['admissions']} | Registrar: {UNIVERSITY_KB['contacts']['registrar']} | IT: {UNIVERSITY_KB['contacts']['it_support']}
- Scholarship: {UNIVERSITY_KB['contacts']['scholarships']}
- Fee deadline: End of Week 4 each semester. Late fee: 10% surcharge.
- Minimum attendance: 70% per course
- Graduation minimum GPA: 2.0

ESCALATION:
- Grade dispute → Course Lecturer → HOD → Academic Affairs
- Fee issue → {UNIVERSITY_KB['contacts']['finance']}
- Mental health → {UNIVERSITY_KB['contacts']['counseling']}
- Technical → {UNIVERSITY_KB['contacts']['it_support']}
- Transcript → {UNIVERSITY_KB['contacts']['registrar']}
"""

    # Role-specific live data
    if role == 'student':
        try:
            profile = user.student_profile
            prog = profile.programme.name if profile.programme else "Not set"
            dept = profile.programme.department.name if profile.programme else "Not set"
            faculty = profile.programme.department.faculty if profile.programme else "Not set"
            courses = list(profile.registrations.filter(
                is_active=True, academic_year=profile.academic_year
            ).select_related('course').values_list('course__code', 'course__name', 'course__credit_hours'))

            # Recent results
            results = list(profile.results.select_related('course').order_by('-academic_year', 'semester')[:8])
            results_text = '\n'.join(
                f"  - {r.course.code} {r.course.name}: {r.grade} ({r.score})" for r in results
            ) or "  No results yet"

            # GPA records
            gpa_records = list(profile.gpa_records.order_by('-academic_year', '-semester')[:4])
            gpa_history = ', '.join(
                f"Sem{r.semester} {r.academic_year}: {r.gpa}" for r in gpa_records
            ) or "No history"

            courses_text = '\n'.join(
                f"  - {c[0]} {c[1]} ({c[2]} credits)" for c in courses
            ) or "  None registered"

            base += f"""
STUDENT LIVE DATA for {name} ({user.user_id}):
- Faculty: {faculty}
- Department: {dept}
- Programme: {prog}
- Level: {profile.level} | Semester: {profile.semester} | Year: {profile.academic_year}
- Cumulative GPA: {profile.cumulative_gpa} ({_gpa_classification(float(profile.cumulative_gpa))})
- GPA History: {gpa_history}
- Gamification: {user.points} points | {user.study_streak} day streak

Enrolled Courses this semester:
{courses_text}

Recent Results:
{results_text}

When the user asks about their GPA, results, courses, or timetable — use this data directly. Do not say you cannot access it."""
        except Exception as e:
            base += f"\nSTUDENT: {name} ({user.user_id}) — live data unavailable."

    elif role == 'staff':
        try:
            profile = user.staff_profile
            dept = profile.department.name if profile.department else "Unknown"
            courses = list(profile.courses_assigned.values_list('code', 'name'))
            courses_text = ', '.join(f"{c[0]} {c[1]}" for c in courses) or "None assigned"
            base += f"""
STAFF LIVE DATA for {name} ({user.user_id}):
- Department: {dept}
- Rank: {profile.get_rank_display()}
- Office: {profile.office or 'Not set'} | Hours: {profile.office_hours or 'Not set'}
- Assigned Courses: {courses_text}"""
        except Exception:
            base += f"\nSTAFF: {name} ({user.user_id})"

    elif role == 'admin':
        base += f"\nADMIN: {name} ({user.user_id}) — full system access."

    # Inject persistent memory
    base += get_user_memory_context(user)

    return base


def _gpa_classification(gpa):
    if gpa >= 3.6: return "First Class"
    elif gpa >= 3.0: return "Second Class Upper"
    elif gpa >= 2.5: return "Second Class Lower"
    elif gpa >= 2.0: return "Third Class"
    return "Below Average"


# ─── NLP Engine (keyword matching + AI fallback) ───────────────────────────────

class NLPEngine:
    def __init__(self):
        self.intents = self._load_intents()
        self.nlp = self._load_spacy()

    def _load_intents(self):
        intents_path = Path(__file__).parent / 'intents.json'
        with open(intents_path, 'r') as f:
            data = json.load(f)
        return data['intents']

    def _load_spacy(self):
        try:
            import spacy
            return spacy.load('en_core_web_sm')
        except Exception:
            return None

    def preprocess(self, text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def match_intent(self, text):
        cleaned = self.preprocess(text)
        best_intent = None
        best_score = 0
        for intent in self.intents:
            if intent['tag'] == 'unknown':
                continue
            score = self._score_intent(cleaned, intent['patterns'])
            if score > best_score:
                best_score = score
                best_intent = intent
        # Raised threshold: only route to keyword handler if clearly matched
        if best_score < 0.6:
            return next(i for i in self.intents if i['tag'] == 'unknown'), 0.0
        return best_intent, best_score

    def _score_intent(self, text, patterns):
        """Score how well text matches an intent's patterns.
        Uses exact word/phrase matching only — no fuzzy similarity to avoid false positives.
        """
        if not patterns:
            return 0
        text_words = set(text.split())
        best = 0
        for pattern in patterns:
            pattern_lower = pattern.lower()
            pattern_words = pattern_lower.split()
            pattern_word_set = set(pattern_words)

            if len(pattern_words) == 1:
                # Single keyword: exact word match only (not substring)
                if pattern_lower in text_words:
                    best = max(best, 0.9)
            else:
                # Multi-word phrase: full phrase must appear in text
                if pattern_lower in text:
                    score = min(1.0, 0.75 + len(pattern_words) * 0.05)
                    best = max(best, score)
                else:
                    # All pattern words must be present in text
                    overlap = len(text_words & pattern_word_set)
                    if overlap == len(pattern_word_set):
                        best = max(best, 0.75)
                    elif overlap >= len(pattern_word_set) * 0.75 and overlap >= 2:
                        best = max(best, 0.65)
        return best

    def get_response(self, intent):
        return random.choice(intent['responses'])

    def extract_entities(self, text):
        entities = {}
        sem_match = re.search(r'semester\s*(\d)', text.lower())
        if sem_match:
            entities['semester'] = int(sem_match.group(1))
        year_match = re.search(r'(20\d{2})', text)
        if year_match:
            entities['year'] = year_match.group(1)
        course_match = re.search(r'([A-Z]{2,4}\s*\d{3,4})', text.upper())
        if course_match:
            entities['course_code'] = course_match.group(1).replace(' ', '')
        return entities


# ─── OpenAI / AI Integration ───────────────────────────────────────────────────

# ─── Gemini AI Integration ────────────────────────────────────────────────────

def call_gemini(system_prompt, conversation_history, user_message):
    """Call Google Gemini API using urllib (no extra package needed)."""
    import urllib.request
    import urllib.error
    import time
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return None

    contents = []
    for turn in conversation_history[-10:]:
        role = 'user' if turn['role'] == 'user' else 'model'
        contents.append({'role': role, 'parts': [{'text': turn['content']}]})
    contents.append({'role': 'user', 'parts': [{'text': user_message}]})

    payload = json.dumps({
        'system_instruction': {'parts': [{'text': system_prompt}]},
        'contents': contents,
        'generationConfig': {
            'maxOutputTokens': 800,
            'temperature': 0.65,
            'topP': 0.9,
        },
        'safetySettings': [
            {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_ONLY_HIGH'},
            {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_ONLY_HIGH'},
        ]
    }).encode('utf-8')

    # Try models in order of preference
    models = ['gemini-2.5-flash-lite', 'gemini-2.0-flash-lite', 'gemini-2.5-flash']
    for model in models:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                candidates = data.get('candidates', [])
                if candidates:
                    return candidates[0]['content']['parts'][0]['text'].strip()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                continue  # Try next model
            break
        except Exception:
            break
    return None


def call_openai(system_prompt, conversation_history, user_message):
    """Call OpenAI API (fallback if OPENAI_API_KEY is set)."""
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-10:]:
            messages.append({"role": turn['role'], "content": turn['content']})
        messages.append({"role": "user", "content": user_message})
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, max_tokens=600, temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def get_conversation_history(session):
    """Get recent conversation turns for AI context."""
    from .models import ChatMessage
    recent = ChatMessage.objects.filter(session=session).order_by('-timestamp')[:20]
    history = []
    for msg in reversed(list(recent)):
        role = 'user' if msg.sender == 'user' else 'assistant'
        history.append({'role': role, 'content': msg.message})
    return history


# ─── Main Chatbot Engine ───────────────────────────────────────────────────────

class ChatbotEngine:
    MOTIVATIONAL_QUOTES = [
        "Success is not final, failure is not fatal: it is the courage to continue that counts. — Churchill",
        "The secret of getting ahead is getting started. — Mark Twain",
        "Education is the most powerful weapon which you can use to change the world. — Mandela",
        "Believe you can and you're halfway there. — Theodore Roosevelt",
        "Hard work beats talent when talent doesn't work hard.",
        "Your GPA doesn't define you, but your effort does.",
        "Every expert was once a beginner. Keep going!",
        "Study hard today so you can live the life you want tomorrow.",
    ]

    MEDITATION_TIPS = [
        "Take 5 deep breaths: inhale for 4 counts, hold for 4, exhale for 4. Repeat.",
        "Close your eyes and focus only on your breathing for 2 minutes.",
        "Try the 5-4-3-2-1 technique: name 5 things you see, 4 you hear, 3 you can touch, 2 you smell, 1 you taste.",
        "Take a 10-minute walk outside. Fresh air clears the mind.",
        "Write down 3 things you're grateful for right now.",
        "Stretch your body for 5 minutes. Tension in the body creates tension in the mind.",
    ]

    STUDY_TIPS = [
        "Use the Pomodoro Technique: 25 minutes focused study, 5 minute break.",
        "Teach what you've learned to someone else — it's the best way to retain information.",
        "Review your notes within 24 hours of a lecture to boost retention by 80%.",
        "Use active recall: close your notes and try to remember key points.",
        "Create mind maps to connect concepts visually.",
        "Study in a clean, quiet environment with your phone on silent.",
        "Get 7-8 hours of sleep — your brain consolidates memory during sleep.",
        "Use past exam questions to guide your study focus.",
    ]

    WELLNESS_TIPS = [
        "🏃 Exercise for at least 30 minutes daily — it boosts brain function and reduces stress.",
        "💧 Stay hydrated. Dehydration reduces concentration by up to 20%.",
        "🥗 Eat balanced meals. Avoid heavy meals before studying.",
        "😴 Aim for 7-8 hours of sleep. Sleep is when your brain consolidates what you learned.",
        "📵 Take digital detox breaks — 10 minutes away from screens every hour.",
        "🧘 Practice mindfulness: even 5 minutes of meditation daily reduces anxiety.",
        "👥 Stay connected with friends and family — social support is vital for mental health.",
    ]

    HELP_TEXT = """Here's everything I can help you with, {name}:

📚 **Academic**
- "What is my GPA?" — Check your current GPA
- "Show my results" — View semester results
- "Show my timetable" — Class schedule
- "My courses" — Registered courses
- "Exam countdown" — Days until your next exam
- "Study plan" — AI-generated personalized study schedule
- "Graduation requirements" — What you need to graduate
- "Improve my GPA" — Personalized tips

🎓 **University Services**
- "Scholarship" — How to apply for scholarships
- "School fees" — Fee payment info & deadlines
- "Transcript" — How to request your transcript
- "Course registration" — Registration guide
- "Admissions" — Entry requirements & application
- "Library" — Digital library & resources
- "Career services" — Jobs, internships, CV help

💪 **Motivation & Wellness**
- "Motivate me" — Get an inspiring quote
- "I'm stressed" — Relaxation & mental health tips
- "Mood check-in" — Track how you're feeling
- "Wellness tips" — Physical & mental health advice
- "Study tips" — How to study better

📋 **Productivity**
- "My tasks" — View planner tasks
- "Study buddy" — Find a study partner
- "Leaderboard" — See your rank & points
- "Morning briefing" — Today's summary
- "My notifications" — Alerts & reminders
- "Upcoming events" — School events

🌍 **Language**
- Ask me in Twi, Ga, Hausa, or Pidgin and I'll respond in kind!

Type anything and I'll do my best to help!"""

    def __init__(self, user, session=None):
        self.user = user
        self.session = session
        self.nlp = NLPEngine()

    def process(self, message, session_context=None):
        """
        Process a message and return a response dict.
        Returns: {'response': str, 'intent': str, 'data': dict, 'mode': str}
        """
        intent, confidence = self.nlp.match_intent(message)
        entities = self.nlp.extract_entities(message)
        tag = intent['tag']

        # If the query mentions another institution, force AI fallback
        # regardless of keyword match
        if self._is_external_query(message):
            ai_response = self._try_ai_fallback(message, session_context)
            if ai_response:
                return {'response': ai_response, 'data': {}, 'mode': 'general',
                        'ai_powered': True, 'intent': 'external', 'confidence': 0.0}

        # Route to specialized handlers
        handlers = {
            'gpa_query': self._handle_gpa,
            'results_query': self._handle_results,
            'timetable_query': self._handle_timetable,
            'next_class': self._handle_next_class,
            'motivation': self._handle_motivation,
            'meditation': self._handle_meditation,
            'study_tips': self._handle_study_tips,
            'notifications': self._handle_notifications,
            'events': self._handle_events,
            'planner': self._handle_planner,
            'gpa_improvement': self._handle_gpa_tips,
            'course_info': self._handle_courses,
            'help': self._handle_help,
            'document_help': self._handle_document_help,
            'scholarship': self._handle_scholarship,
            'fees': self._handle_fees,
            'graduation': self._handle_graduation,
            'admissions': self._handle_admissions,
            'library': self._handle_library,
            'career': self._handle_career,
            'wellness': self._handle_wellness,
            'contact': self._handle_contact,
            'staff_info': self._handle_staff_info,
            'attendance': self._handle_attendance,
            'exam_info': self._handle_exam_info,
            # New handlers
            'exam_countdown': self._handle_exam_countdown,
            'course_registration': self._handle_course_registration,
            'transcript': self._handle_transcript,
            'mood_checkin': self._handle_mood_checkin,
            'study_plan': self._handle_study_plan,
            'study_buddy': self._handle_study_buddy,
            'leaderboard': self._handle_leaderboard,
            'morning_briefing': self._handle_morning_briefing,
        }

        if tag in handlers:
            response_data = handlers[tag](entities, session_context)
        else:
            # unknown intent or low-confidence match — try AI first
            ai_response = self._try_ai_fallback(message, session_context)
            if ai_response:
                response_data = {'response': ai_response, 'data': {}, 'mode': 'general', 'ai_powered': True}
            else:
                response_text = self.nlp.get_response(intent)
                response_data = {'response': response_text, 'data': {}}

        response_data['intent'] = tag
        response_data['confidence'] = round(confidence, 2)
        return response_data

    def _is_external_query(self, message):
        """Detect if the query is about another institution or clearly off-topic for KAAF."""
        text = message.lower()
        # Other universities / institutions
        external_institutions = [
            'university of ghana', 'ug ', 'legon', 'knust', 'ashesi',
            'central university', 'ghana institute', 'ucc', 'uds', 'uew',
            'harvard', 'oxford', 'cambridge', 'mit', 'stanford',
            'accra technical', 'polytechnic',
        ]
        for inst in external_institutions:
            if inst in text:
                return True
        # Comparative questions about other places
        comparative_patterns = [
            r'\bat\s+(?!kaaf)\w+\s+university',
            r'\bof\s+(?!kaaf)\w+\s+university',
        ]
        for pattern in comparative_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _try_ai_fallback(self, message, session_context):
        """Use Gemini as the AI brain with full live context injected."""
        try:
            system_prompt = build_system_prompt(self.user)
            history = get_conversation_history(self.session) if self.session else []
            return call_gemini(system_prompt, history, message) or \
                   call_openai(system_prompt, history, message)
        except Exception:
            return None

    def _get_live_context(self):
        """Gather live user data to inject into AI context."""
        ctx = {}
        try:
            if self.user.is_student:
                profile = self.user.student_profile
                ctx['gpa'] = float(profile.cumulative_gpa)
                ctx['level'] = profile.level
                ctx['semester'] = profile.semester
                ctx['academic_year'] = profile.academic_year
                ctx['programme'] = profile.programme.name if profile.programme else None
                ctx['points'] = self.user.points
                ctx['streak'] = self.user.study_streak
        except Exception:
            pass
        return json.dumps(ctx) if ctx else None

    # ── Academic Handlers ──────────────────────────────────────────────────────

    def _handle_gpa(self, entities, context):
        try:
            profile = self.user.student_profile
            gpa = float(profile.cumulative_gpa)
            level_text = self._gpa_level_text(gpa)
            response = (
                f"📊 **Your Academic Standing, {self.user.first_name}:**\n\n"
                f"**Cumulative GPA: {gpa:.2f}** — {level_text}\n\n"
                f"- Level: {profile.level} | Semester: {profile.semester}\n"
                f"- Academic Year: {profile.academic_year}\n"
                f"- Programme: {profile.programme.name if profile.programme else 'N/A'}\n\n"
                f"💡 Type **'improve my GPA'** for personalized tips, or **'show my results'** to see your grades."
            )
            return {'response': response, 'data': {'gpa': gpa}, 'mode': 'academic'}
        except Exception:
            return {'response': "I couldn't retrieve your GPA. Please check your profile or contact the Registrar.", 'data': {}}

    def _gpa_level_text(self, gpa):
        if gpa >= 3.6: return "First Class 🏆"
        elif gpa >= 3.0: return "Second Class Upper 🥇"
        elif gpa >= 2.5: return "Second Class Lower 🥈"
        elif gpa >= 2.0: return "Third Class 🥉"
        else: return "Below Average — Let's work on improving this! 💪"

    def _handle_results(self, entities, context):
        try:
            profile = self.user.student_profile
            results = profile.results.select_related('course').order_by('-academic_year', 'semester')[:10]
            if not results:
                return {'response': "No results found yet. Check back after exams are graded.", 'data': {}}
            lines = [f"📊 **Your Recent Results, {self.user.first_name}:**\n"]
            for r in results:
                lines.append(f"• **{r.course.code}** — {r.course.name}: **{r.grade}** ({r.score})")
            lines.append(f"\n**Cumulative GPA: {profile.cumulative_gpa}**")
            lines.append("\n💡 Visit the **Results** page for full semester breakdown.")
            return {'response': '\n'.join(lines), 'data': {'count': len(results)}, 'mode': 'academic'}
        except Exception:
            return {'response': "Couldn't load results. Please try again or visit the Results page.", 'data': {}}

    def _handle_timetable(self, entities, context):
        try:
            from django.utils import timezone
            profile = self.user.student_profile
            today = timezone.now().strftime('%A')[:3].upper()
            registered = profile.registrations.filter(is_active=True).values_list('course_id', flat=True)
            from apps.students.models import Timetable
            entries = Timetable.objects.filter(
                course_id__in=registered, day=today,
                academic_year=profile.academic_year,
            ).select_related('course').order_by('start_time')
            if not entries:
                return {'response': f"📅 No classes scheduled for today. Enjoy your free time, {self.user.first_name}! 😊\n\n💡 Visit the **Timetable** page to see your full weekly schedule.", 'data': {}}
            lines = [f"📅 **Today's Schedule ({today}), {self.user.first_name}:**\n"]
            for e in entries:
                lines.append(f"• **{e.start_time.strftime('%H:%M')} – {e.end_time.strftime('%H:%M')}**: {e.course.name} @ {e.venue}")
            lines.append("\n💡 Type **'next class'** to see your upcoming class.")
            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'academic'}
        except Exception:
            return {'response': "Couldn't load timetable. Please check the Timetable page.", 'data': {}}

    def _handle_next_class(self, entities, context):
        try:
            from django.utils import timezone
            from apps.students.models import Timetable
            profile = self.user.student_profile
            now = timezone.now()
            today = now.strftime('%A')[:3].upper()
            registered = profile.registrations.filter(is_active=True).values_list('course_id', flat=True)
            entry = Timetable.objects.filter(
                course_id__in=registered, day=today,
                academic_year=profile.academic_year,
                start_time__gt=now.time(),
            ).select_related('course').order_by('start_time').first()
            if entry:
                response = f"⏰ Your next class is **{entry.course.name}** at **{entry.start_time.strftime('%H:%M')}** in {entry.venue}.\n\n💡 Set a reminder in your **Planner** so you don't miss it!"
            else:
                response = f"No more classes today, {self.user.first_name}! 😊 Time to review your notes or relax.\n\n💡 Check your **Timetable** for tomorrow's schedule."
            return {'response': response, 'data': {}, 'mode': 'academic'}
        except Exception:
            return {'response': "Couldn't find your next class. Check your timetable.", 'data': {}}

    def _handle_courses(self, entities, context):
        try:
            profile = self.user.student_profile
            registrations = profile.registrations.filter(
                is_active=True, academic_year=profile.academic_year
            ).select_related('course')
            if not registrations:
                return {'response': "No courses registered for this semester. Contact the Registrar if this is an error.", 'data': {}}
            lines = [f"📚 **Your Registered Courses ({profile.academic_year} Sem {profile.semester}):**\n"]
            total_credits = 0
            for reg in registrations:
                lines.append(f"• **{reg.course.code}** — {reg.course.name} ({reg.course.credit_hours} credits)")
                total_credits += reg.course.credit_hours
            lines.append(f"\n**Total Credit Hours: {total_credits}**")
            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'academic'}
        except Exception:
            return {'response': "Couldn't load courses.", 'data': {}}

    def _handle_attendance(self, entities, context):
        response = (
            f"📋 **Attendance Policy at KAAF University:**\n\n"
            f"- Minimum attendance required: **70%** per course\n"
            f"- Falling below 70% may bar you from sitting exams\n"
            f"- AI alerts are sent when your attendance drops below threshold\n\n"
            f"**To check your attendance:**\n"
            f"• Visit the **Timetable** page for session records\n"
            f"• Contact your course lecturer directly\n"
            f"• Email the Registrar: {UNIVERSITY_KB['contacts']['registrar']}\n\n"
            f"💡 Make sure to attend all classes, {self.user.first_name}!"
        )
        return {'response': response, 'data': {}, 'mode': 'academic'}

    def _handle_exam_info(self, entities, context):
        try:
            from apps.notifications.models import Event
            from django.utils import timezone
            exams = Event.objects.filter(
                event_type='exam', date__gte=timezone.now().date()
            ).order_by('date')[:5]
            lines = [f"📝 **Upcoming Exams, {self.user.first_name}:**\n"]
            if exams:
                for e in exams:
                    lines.append(f"• **{e.title}** — {e.date.strftime('%B %d, %Y')} | {e.location or 'TBA'}")
            else:
                lines.append("No upcoming exams scheduled at the moment.")
            lines.append(f"\n**Exam Rules:**\n• Arrive 15 minutes early\n• Bring your student ID\n• No electronic devices unless permitted\n\n💡 Contact the Examinations Office for specific exam timetables.")
            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'academic'}
        except Exception:
            return {'response': "Contact the Examinations Office for exam schedules.", 'data': {}}

    # ── Motivation & Wellness Handlers ─────────────────────────────────────────

    def _handle_motivation(self, entities, context):
        quote = random.choice(self.MOTIVATIONAL_QUOTES)
        response = (
            f"💪 **Here's your motivation, {self.user.first_name}:**\n\n"
            f"_{quote}_\n\n"
            f"You've got this! Keep pushing forward. 🚀\n\n"
            f"💡 Type **'study tips'** for practical advice, or **'my tasks'** to stay on track."
        )
        return {'response': response, 'data': {}, 'mode': 'motivation'}

    def _handle_meditation(self, entities, context):
        tip = random.choice(self.MEDITATION_TIPS)
        response = (
            f"🧘 **Take a moment to breathe, {self.user.first_name}:**\n\n"
            f"{tip}\n\n"
            f"Remember: your mental health matters as much as your grades. "
            f"If you're feeling overwhelmed, please reach out:\n"
            f"- **Campus Counselor**: {UNIVERSITY_KB['contacts']['counseling']}\n"
            f"- **Crisis Line**: {UNIVERSITY_KB['crisis_lines'][0]}\n\n"
            f"💡 You can also book an appointment with the campus counselor."
        )
        return {'response': response, 'data': {}, 'mode': 'mental_health'}

    def _handle_wellness(self, entities, context):
        tips = random.sample(self.WELLNESS_TIPS, min(3, len(self.WELLNESS_TIPS)))
        lines = [f"🌟 **Wellness Tips for You, {self.user.first_name}:**\n"]
        for tip in tips:
            lines.append(f"• {tip}")
        lines.append(f"\n**Campus Resources:**\n• Health Center: {UNIVERSITY_KB['contacts']['health']}\n• Counseling: {UNIVERSITY_KB['contacts']['counseling']}")
        lines.append("\n💡 Your wellbeing is a priority. Don't hesitate to seek help!")
        return {'response': '\n'.join(lines), 'data': {}, 'mode': 'mental_health'}

    def _handle_study_tips(self, entities, context):
        tips = random.sample(self.STUDY_TIPS, min(3, len(self.STUDY_TIPS)))
        lines = [f"📖 **Study Tips for {self.user.first_name}:**\n"]
        for i, tip in enumerate(tips, 1):
            lines.append(f"{i}. {tip}")
        lines.append("\n💡 Try the **Pomodoro Timer** in your Planner for focused study sessions!")
        return {'response': '\n'.join(lines), 'data': {}, 'mode': 'productivity'}

    # ── Productivity Handlers ──────────────────────────────────────────────────

    def _handle_notifications(self, entities, context):
        try:
            from apps.notifications.models import Notification
            notifs = Notification.objects.filter(user=self.user, is_read=False).order_by('-created_at')[:5]
            if not notifs:
                return {'response': f"✅ No unread notifications, {self.user.first_name}. You're all caught up!\n\n💡 Visit the **Notifications** page to see your full history.", 'data': {}}
            lines = [f"🔔 **You have {notifs.count()} unread notification(s):**\n"]
            for n in notifs:
                lines.append(f"• **{n.title}**: {n.message[:80]}...")
            lines.append("\n💡 Visit the **Notifications** page to mark them as read.")
            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'academic'}
        except Exception:
            return {'response': "Couldn't load notifications.", 'data': {}}

    def _handle_events(self, entities, context):
        try:
            from apps.notifications.models import Event
            from django.utils import timezone
            events = Event.objects.filter(date__gte=timezone.now().date()).order_by('date')[:5]
            if not events:
                return {'response': "No upcoming events at the moment. Check back later!", 'data': {}}
            lines = ["📅 **Upcoming Events at KAAF University:**\n"]
            for e in events:
                lines.append(f"• **{e.title}** — {e.date.strftime('%B %d, %Y')} | {e.location or 'TBA'}")
            lines.append("\n💡 Visit the **Notifications** page for full event details.")
            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'academic'}
        except Exception:
            return {'response': "Couldn't load events.", 'data': {}}

    def _handle_planner(self, entities, context):
        try:
            from apps.planner.models import Task
            tasks = Task.objects.filter(user=self.user, is_completed=False).order_by('due_date', 'priority')[:5]
            if not tasks:
                return {'response': f"🎉 No pending tasks, {self.user.first_name}! Add some in your **Planner**.\n\n💡 Use the Planner to track assignments, study sessions, and deadlines.", 'data': {}}
            lines = [f"📋 **Your Pending Tasks, {self.user.first_name}:**\n"]
            for t in tasks:
                due = t.due_date.strftime('%b %d') if t.due_date else 'No deadline'
                overdue = " ⚠️ OVERDUE" if t.is_overdue else ""
                lines.append(f"• [{t.get_priority_display()}] **{t.title}** — Due: {due}{overdue}")
            lines.append("\n💡 Visit your **Planner** to manage tasks and start a study timer.")
            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'productivity'}
        except Exception:
            return {'response': "Couldn't load tasks.", 'data': {}}

    def _handle_document_help(self, entities, context):
        try:
            profile = self.user.student_profile
            docs = profile.documents.filter(processed=True).order_by('-uploaded_at')[:3]
            if not docs:
                return {'response': "No processed documents found. Upload a PDF in the **Documents** section and I'll summarize it for you!\n\n💡 Supported formats: PDF, DOCX", 'data': {}}
            lines = [f"📄 **Your Recent Documents, {self.user.first_name}:**\n"]
            for d in docs:
                lines.append(f"• **{d.title}** — {d.summary[:100]}...")
            lines.append("\n💡 Go to the **Documents** page to see full summaries and key points.")
            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'academic'}
        except Exception:
            return {'response': "Upload a document in the **Documents** section and I'll help summarize it!", 'data': {}}

    # ── University Services Handlers ───────────────────────────────────────────

    def _handle_scholarship(self, entities, context):
        try:
            profile = self.user.student_profile
            gpa = float(profile.cumulative_gpa)
            eligible = gpa >= 3.0
            status = "✅ You may be eligible based on your GPA!" if eligible else "⚠️ Most scholarships require a minimum GPA of 3.0. Keep working on improving your grades!"
            response = (
                f"🎓 **Scholarship Information at KAAF University**\n\n"
                f"{status} (Your GPA: **{gpa:.2f}**)\n\n"
                f"**Available Scholarships:**\n"
                f"• **Merit Scholarship** — GPA ≥ 3.6 (First Class). Up to 50% tuition.\n"
                f"• **Academic Excellence Award** — GPA ≥ 3.0. Partial tuition support.\n"
                f"• **Need-Based Bursary** — Financial need. Contact Finance Office.\n"
                f"• **Departmental Scholarship** — Check with your HOD.\n"
                f"• **Government Scholarship** — Ghana Scholarship Secretariat. Visit scholarships.gov.gh\n\n"
                f"**How to Apply:**\n"
                f"• Visit **Student Affairs Office** (Admin Block, Room 12)\n"
                f"• Submit: Application form, transcripts, recommendation letter, financial statement\n"
                f"• Deadline: End of first semester each academic year\n\n"
                f"📧 **Contact:** {UNIVERSITY_KB['contacts']['scholarships']}\n\n"
                f"💡 Type **'improve my GPA'** for tips to boost your eligibility!"
            )
        except Exception:
            response = (
                f"🎓 **Scholarship Information at KAAF University**\n\n"
                f"**Types:** Merit, Need-Based Bursary, Departmental, Government\n"
                f"**Apply at:** Student Affairs Office (Admin Block, Room 12)\n"
                f"**Requirements:** Application form, transcripts, recommendation letter\n"
                f"**Deadline:** End of first semester\n\n"
                f"📧 {UNIVERSITY_KB['contacts']['scholarships']}"
            )
        return {'response': response, 'data': {}, 'mode': 'academic'}

    def _handle_fees(self, entities, context):
        response = (
            f"💰 **Fee Information at KAAF University**\n\n"
            f"**Payment Methods:**\n"
            + '\n'.join(f"• {m}" for m in UNIVERSITY_KB['payment_methods']) +
            f"\n\n**Important Deadlines:**\n"
            f"• Fees must be paid before the end of **Week 4** each semester\n"
            f"• Late payment attracts a **10% surcharge**\n"
            f"• Financial clearance required for exams and graduation\n\n"
            f"**Payment Plans:** Installment plans available — contact Finance Office\n\n"
            f"📧 **Finance Office:** {UNIVERSITY_KB['contacts']['finance']}\n"
            f"📍 Admin Block, Ground Floor\n\n"
            f"💡 Log in to the student portal to check your outstanding balance."
        )
        return {'response': response, 'data': {}, 'mode': 'academic'}

    def _handle_graduation(self, entities, context):
        try:
            profile = self.user.student_profile
            total_credits = sum(r.course.credit_hours for r in profile.results.select_related('course'))
            response = (
                f"🎓 **Graduation Requirements for {self.user.first_name}**\n\n"
                f"**Your Progress:**\n"
                f"• Level: **{profile.level}** | Year: **{profile.academic_year}**\n"
                f"• Cumulative GPA: **{profile.cumulative_gpa}**\n"
                f"• Credits Earned: **{total_credits}**\n\n"
                f"**Requirements to Graduate:**\n"
                f"• Minimum Cumulative GPA of **2.0**\n"
                f"• Complete all required courses (typically **120+ credit hours**)\n"
                f"• No outstanding fees\n"
                f"• Complete industrial attachment (if applicable)\n"
                f"• Submit and defend final year project (Level 400)\n\n"
                f"**Graduation Ceremony:** Held annually in **July/August**\n\n"
                f"📧 Contact the **Examinations Office** for programme-specific requirements."
            )
        except Exception:
            response = (
                f"🎓 **Graduation Requirements:**\n\n"
                f"• Minimum GPA: **2.0**\n• Complete all required courses (120+ credit hours)\n"
                f"• No outstanding fees\n• Final year project (Level 400)\n\n"
                f"Contact the Examinations Office for details."
            )
        return {'response': response, 'data': {}, 'mode': 'academic'}

    def _handle_admissions(self, entities, context):
        response = (
            f"🏫 **Admissions at KAAF University**\n\n"
            f"**Entry Requirements:**\n"
            f"• WASSCE/SSSCE with minimum grades (varies by programme)\n"
            f"• HND holders may qualify for direct entry to Level 200/300\n"
            f"• Postgraduate: First degree with minimum Second Class Lower\n\n"
            f"**Application Process:**\n"
            f"1. Visit the KAAF University website or Admissions Office\n"
            f"2. Complete the online application form\n"
            f"3. Upload required documents (certificates, ID, passport photo)\n"
            f"4. Pay application fee\n"
            f"5. Track your application status online\n\n"
            f"**Available Programmes:**\n"
            + '\n'.join(f"• {f['name']} ({f['code']})" for f in UNIVERSITY_KB['faculties']) +
            f"\n\n📧 **Admissions Office:** {UNIVERSITY_KB['contacts']['admissions']}\n\n"
            f"💡 Book a campus tour to see KAAF University in person!"
        )
        return {'response': response, 'data': {}, 'mode': 'general'}

    def _handle_library(self, entities, context):
        response = (
            f"📚 **KAAF University Library Services**\n\n"
            f"**Available Resources:**\n"
            f"• Physical books and journals\n"
            f"• Digital e-books and research papers\n"
            f"• Past exam question papers\n"
            f"• Online databases (JSTOR, Google Scholar access)\n\n"
            f"**Services:**\n"
            f"• Book borrowing (up to 3 books, 2 weeks)\n"
            f"• E-book reading in-app\n"
            f"• Reference generator (APA, MLA, Chicago)\n"
            f"• Research assistance from librarians\n"
            f"• Reserve books in advance\n\n"
            f"**Library Hours:** Mon–Fri: 7am–9pm | Sat: 8am–5pm\n\n"
            f"📧 **Library:** {UNIVERSITY_KB['contacts']['library']}\n\n"
            f"💡 AI can recommend resources based on your enrolled courses — just ask!"
        )
        return {'response': response, 'data': {}, 'mode': 'academic'}

    def _handle_career(self, entities, context):
        response = (
            f"💼 **Career Services at KAAF University, {self.user.first_name}**\n\n"
            f"**What We Offer:**\n"
            f"• Browse internship and job listings\n"
            f"• AI-powered CV review and scoring\n"
            f"• Mock interview practice\n"
            f"• Career counseling appointments\n"
            f"• Alumni mentorship connections\n"
            f"• Workshop and training events\n"
            f"• Employer partnerships directory\n"
            f"• NYSC / National Service information\n\n"
            f"**CV Tips:**\n"
            f"• Keep it to 1-2 pages\n"
            f"• Tailor it to each job application\n"
            f"• Include your GPA if it's 3.0 or above\n"
            f"• Highlight projects and extracurriculars\n\n"
            f"📧 **Career Services:** {UNIVERSITY_KB['contacts']['career']}\n\n"
            f"💡 Book a career counseling session today!"
        )
        return {'response': response, 'data': {}, 'mode': 'general'}

    def _handle_contact(self, entities, context):
        lines = [f"📞 **KAAF University Key Contacts:**\n"]
        contact_labels = {
            'admissions': '🏫 Admissions Office',
            'scholarships': '🎓 Scholarships',
            'finance': '💰 Finance / Bursary',
            'registrar': '📋 Registrar',
            'it_support': '💻 IT Support',
            'health': '🏥 Health Center',
            'counseling': '🧘 Counseling',
            'career': '💼 Career Services',
            'library': '📚 Library',
            'general': '📧 General Enquiries',
        }
        for key, label in contact_labels.items():
            lines.append(f"• {label}: {UNIVERSITY_KB['contacts'][key]}")
        lines.append("\n💡 For urgent matters, visit the relevant office in person at the Admin Block.")
        return {'response': '\n'.join(lines), 'data': {}, 'mode': 'general'}

    def _handle_staff_info(self, entities, context):
        if self.user.is_staff_member:
            try:
                profile = self.user.staff_profile
                courses = list(profile.courses_assigned.values_list('name', flat=True))
                response = (
                    f"👨‍🏫 **Your Staff Profile, {self.user.first_name}:**\n\n"
                    f"• Department: {profile.department.name if profile.department else 'N/A'}\n"
                    f"• Rank: {profile.get_rank_display()}\n"
                    f"• Office: {profile.office or 'Not set'}\n"
                    f"• Office Hours: {profile.office_hours or 'Not set'}\n"
                    f"• Courses: {', '.join(courses) if courses else 'None assigned'}\n\n"
                    f"💡 Visit the **Staff Dashboard** to manage grades and student performance."
                )
            except Exception:
                response = "Visit the **Staff Dashboard** to manage your courses and students."
        else:
            response = "Staff information is only available to authenticated staff members."
        return {'response': response, 'data': {}, 'mode': 'general'}

    def _handle_gpa_tips(self, entities, context):
        try:
            profile = self.user.student_profile
            from apps.students.services import GPAAnalyzer
            analyzer = GPAAnalyzer(profile)
            tips = analyzer.get_improvement_tips()
            lines = [f"📈 **GPA Improvement Tips for {self.user.first_name}:**\n"]
            for i, tip in enumerate(tips, 1):
                lines.append(f"{i}. {tip}")
            lines.append("\n💡 Use the **Study Timer** in your Planner for focused study sessions!")
            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'academic'}
        except Exception:
            tips = random.sample(self.STUDY_TIPS, 3)
            return {'response': f"📈 **Tips to Improve Your GPA:**\n\n" + '\n'.join(f"• {t}" for t in tips), 'data': {}}

    def _handle_help(self, entities, context):
        return {'response': self.HELP_TEXT.format(name=self.user.first_name), 'data': {}, 'mode': 'general'}

    # ── New Feature Handlers ───────────────────────────────────────────────────

    def _handle_exam_countdown(self, entities, context):
        try:
            from apps.notifications.models import Event
            from django.utils import timezone
            today = timezone.now().date()
            exams = Event.objects.filter(
                event_type='exam', date__gte=today
            ).order_by('date')[:5]
            if not exams:
                return {'response': f"No upcoming exams found in the system, {self.user.first_name}. Check with your lecturer or the Examinations Office.", 'data': {}}
            lines = [f"⏳ **Exam Countdown for {self.user.first_name}:**\n"]
            for e in exams:
                days = (e.date - today).days
                urgency = "🔴" if days <= 3 else "🟡" if days <= 7 else "🟢"
                lines.append(f"{urgency} **{e.title}** — {e.date.strftime('%B %d, %Y')} ({days} day{'s' if days != 1 else ''} away) | {e.location or 'TBA'}")
            lines.append("\n💡 Type **'study plan'** and I'll create a personalized study schedule for you!")
            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'academic'}
        except Exception:
            return {'response': "Couldn't load exam schedule. Check the Notifications page or contact the Examinations Office.", 'data': {}}

    def _handle_course_registration(self, entities, context):
        try:
            profile = self.user.student_profile
            registered = profile.registrations.filter(
                is_active=True, academic_year=profile.academic_year
            ).select_related('course')
            reg_count = registered.count()
            response = (
                f"📋 **Course Registration Guide, {self.user.first_name}:**\n\n"
                f"**Your Current Status:** {reg_count} course(s) registered for {profile.academic_year} Sem {profile.semester}\n\n"
                f"**How to Register:**\n"
                f"1. Visit the **Registrar's Office** (Admin Block) or the student portal\n"
                f"2. Confirm you have no outstanding fees (financial clearance required)\n"
                f"3. Select courses for your level ({profile.level}) and semester\n"
                f"4. Check for timetable clashes before confirming\n"
                f"5. Get your adviser's signature if required\n\n"
                f"**Registration Deadlines:** Usually end of Week 2 each semester\n"
                f"**Late registration fee:** May apply after deadline\n\n"
                f"📧 **Registrar:** {UNIVERSITY_KB['contacts']['registrar']}\n\n"
                f"💡 Type **'my courses'** to see what you're currently registered for."
            )
            return {'response': response, 'data': {}, 'mode': 'academic'}
        except Exception:
            return {'response': f"For course registration, visit the Registrar's Office or contact {UNIVERSITY_KB['contacts']['registrar']}.", 'data': {}}

    def _handle_transcript(self, entities, context):
        response = (
            f"📄 **Transcript Request, {self.user.first_name}:**\n\n"
            f"**How to Request:**\n"
            f"1. Visit the **Registrar's Office** in person\n"
            f"2. Complete the Transcript Request Form\n"
            f"3. Pay the transcript fee at the Finance Office\n"
            f"4. Provide your student ID and purpose of request\n"
            f"5. Processing time: **5–10 working days** (official), **2–3 days** (unofficial)\n\n"
            f"**Types Available:**\n"
            f"• Official (sealed, for external use)\n"
            f"• Unofficial (for personal reference)\n"
            f"• Electronic (email delivery available)\n\n"
            f"📧 **Registrar:** {UNIVERSITY_KB['contacts']['registrar']}\n"
            f"📍 Admin Block, 1st Floor\n\n"
            f"💡 Make sure you have financial clearance before requesting."
        )
        return {'response': response, 'data': {}, 'mode': 'academic'}

    def _handle_mood_checkin(self, entities, context):
        from apps.accounts.models import MoodCheckIn
        # Check recent mood
        recent = MoodCheckIn.objects.filter(user=self.user).order_by('-created_at')[:3]
        if recent:
            avg = sum(m.mood for m in recent) / len(recent)
            trend = "improving 📈" if len(recent) >= 2 and recent[0].mood > recent[1].mood else \
                    "declining 📉" if len(recent) >= 2 and recent[0].mood < recent[1].mood else "stable ➡️"
            last_mood = dict(MoodCheckIn.MOOD_CHOICES).get(recent[0].mood, '')
            response = (
                f"💭 **Mood Check-In, {self.user.first_name}:**\n\n"
                f"Your last check-in: **{last_mood}**\n"
                f"Recent trend: **{trend}**\n\n"
                f"How are you feeling right now? Reply with a number:\n"
                f"5 — 😄 Great | 4 — 🙂 Good | 3 — 😐 Okay | 2 — 😔 Low | 1 — 😢 Struggling\n\n"
            )
            if avg <= 2:
                response += f"⚠️ I notice you've been feeling low lately. Please reach out:\n• Campus Counselor: {UNIVERSITY_KB['contacts']['counseling']}\n• Crisis Line: {UNIVERSITY_KB['crisis_lines'][0]}"
        else:
            response = (
                f"💭 **Mood Check-In, {self.user.first_name}:**\n\n"
                f"How are you feeling today? Reply with a number:\n"
                f"5 — 😄 Great | 4 — 🙂 Good | 3 — 😐 Okay | 2 — 😔 Low | 1 — 😢 Struggling\n\n"
                f"I track your mood over time to help you stay well. Your responses are private."
            )
        return {'response': response, 'data': {}, 'mode': 'mental_health'}

    def _handle_study_plan(self, entities, context):
        try:
            from apps.notifications.models import Event
            from apps.students.models import Timetable
            from django.utils import timezone
            profile = self.user.student_profile
            today = timezone.now().date()

            # Get upcoming exams
            exams = list(Event.objects.filter(event_type='exam', date__gte=today).order_by('date')[:3])
            # Get enrolled courses
            courses = list(profile.registrations.filter(
                is_active=True, academic_year=profile.academic_year
            ).values_list('course__name', flat=True))

            if not courses:
                return {'response': f"You don't have any registered courses yet, {self.user.first_name}. Register your courses first, then I can create a study plan!", 'data': {}}

            # Build context for Gemini to generate the plan
            exam_info = '\n'.join(f"- {e.title}: {e.date.strftime('%B %d')}" for e in exams) or "No exams scheduled yet"
            course_list = ', '.join(courses)

            prompt = (
                f"Create a practical 2-week study plan for {self.user.first_name}, a Level {profile.level} student at KAAF University.\n"
                f"Enrolled courses: {course_list}\n"
                f"Upcoming exams:\n{exam_info}\n"
                f"Current GPA: {profile.cumulative_gpa}\n\n"
                f"Format: Day-by-day schedule with specific subjects and study techniques. Keep it motivating and realistic. Max 300 words."
            )
            system = f"You are KAAF AI, a helpful academic assistant. Create personalized, practical study plans."
            from apps.chatbot.nlp_engine import call_gemini as _call_gemini
            plan = _call_gemini(system, [], prompt)
            if plan:
                return {'response': f"📚 **Your Personalized Study Plan, {self.user.first_name}:**\n\n{plan}\n\n💡 Add study sessions to your **Planner** to track your progress!", 'data': {}, 'mode': 'productivity'}
            else:
                return {'response': f"📚 **Quick Study Plan for {self.user.first_name}:**\n\nFor each of your {len(courses)} courses:\n• 2 hours daily review\n• Focus on past questions\n• Use the Pomodoro technique (25min study / 5min break)\n• Review notes within 24 hours of lectures\n\n💡 Add tasks to your **Planner** to stay on track!", 'data': {}, 'mode': 'productivity'}
        except Exception:
            return {'response': "I'll help you create a study plan! Tell me which subjects you want to focus on and when your exams are.", 'data': {}}

    def _handle_study_buddy(self, entities, context):
        try:
            from apps.accounts.models import StudyBuddy
            profile = self.user.student_profile
            courses = list(profile.registrations.filter(
                is_active=True, academic_year=profile.academic_year
            ).values_list('course__name', flat=True))

            # Check existing buddy
            existing = StudyBuddy.objects.filter(
                requester=self.user, status='active'
            ).select_related('buddy').first()

            if existing and existing.buddy:
                response = (
                    f"👥 **Your Study Buddy, {self.user.first_name}:**\n\n"
                    f"You're currently paired with **{existing.buddy.get_full_name()}** ({existing.buddy.user_id})\n"
                    f"Course: {existing.course.name if existing.course else 'General'}\n\n"
                    f"💡 Reach out to your buddy and schedule a study session!"
                )
            else:
                # Find a potential match in same programme and level
                potential = profile.__class__.objects.filter(
                    programme=profile.programme,
                    level=profile.level,
                    academic_year=profile.academic_year,
                ).exclude(user=self.user).select_related('user').first()

                if potential:
                    response = (
                        f"👥 **Study Buddy Match, {self.user.first_name}!**\n\n"
                        f"I found a potential study buddy for you:\n"
                        f"**{potential.user.first_name}** — Level {potential.level}, {profile.programme.name if profile.programme else 'Same Programme'}\n\n"
                        f"You're both studying the same courses. Connect through the group chat or ask your lecturer to introduce you.\n\n"
                        f"💡 Study buddies improve exam scores by up to 30%!"
                    )
                else:
                    response = (
                        f"👥 **Study Buddy, {self.user.first_name}:**\n\n"
                        f"No matches found in your programme right now. Try:\n"
                        f"• Joining your class **Group Chat** to find study partners\n"
                        f"• Asking your lecturer to organize study groups\n"
                        f"• Visiting the **Student Affairs Office** for study group listings\n\n"
                        f"💡 Your courses: {', '.join(courses[:3]) if courses else 'None registered'}"
                    )
            return {'response': response, 'data': {}, 'mode': 'productivity'}
        except Exception:
            return {'response': "Join your class group chat to find study partners!", 'data': {}}

    def _handle_leaderboard(self, entities, context):
        try:
            from apps.accounts.models import User
            top = User.objects.filter(role='student', is_active=True).order_by('-points')[:5]
            my_rank = User.objects.filter(
                role='student', is_active=True, points__gt=self.user.points
            ).count() + 1

            lines = [f"🏆 **Leaderboard — Top Students:**\n"]
            medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
            for i, u in enumerate(top):
                marker = " ← You!" if u.id == self.user.id else ""
                lines.append(f"{medals[i]} **{u.get_full_name()}** — {u.points} pts | 🔥 {u.study_streak}d{marker}")

            lines.append(f"\n**Your Rank: #{my_rank}** with **{self.user.points} points** and a **{self.user.study_streak}-day streak** 🔥")

            if my_rank == 1:
                lines.append("\n🎉 You're #1! Keep it up!")
            elif my_rank <= 3:
                lines.append(f"\n💪 You're in the top 3! Keep studying to stay there!")
            else:
                gap = top[0].points - self.user.points if top else 0
                lines.append(f"\n💡 You're {gap} points away from #1. Complete tasks and study sessions to earn more points!")

            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'motivation'}
        except Exception:
            return {'response': f"You have **{self.user.points} points** and a **{self.user.study_streak}-day streak**! Keep it up! 🔥", 'data': {}}

    def _handle_morning_briefing(self, entities, context):
        try:
            from django.utils import timezone
            from apps.notifications.models import Notification, Event
            from apps.planner.models import Task
            from apps.students.models import Timetable

            now = timezone.now()
            today = now.strftime('%A')[:3].upper()
            today_date = now.date()

            lines = [f"☀️ **Good morning, {self.user.first_name}!** Here's your day at a glance:\n"]

            # Today's classes
            try:
                profile = self.user.student_profile
                registered = profile.registrations.filter(is_active=True).values_list('course_id', flat=True)
                classes = Timetable.objects.filter(
                    course_id__in=registered, day=today,
                    academic_year=profile.academic_year,
                ).select_related('course').order_by('start_time')
                if classes:
                    lines.append(f"📅 **Today's Classes ({len(classes)}):**")
                    for c in classes:
                        lines.append(f"  • {c.start_time.strftime('%H:%M')} — {c.course.name} @ {c.venue}")
                else:
                    lines.append("📅 No classes today — great day to catch up on reading!")
            except Exception:
                pass

            # Pending tasks
            pending = Task.objects.filter(user=self.user, is_completed=False).count()
            overdue = Task.objects.filter(user=self.user, is_completed=False, due_date__lt=today_date).count()
            lines.append(f"\n✅ **Tasks:** {pending} pending" + (f" | ⚠️ {overdue} overdue" if overdue else ""))

            # Unread notifications
            unread = Notification.objects.filter(user=self.user, is_read=False).count()
            if unread:
                lines.append(f"🔔 **{unread} unread notification(s)**")

            # Upcoming events
            events = Event.objects.filter(date__gte=today_date).order_by('date')[:2]
            if events:
                lines.append(f"\n📌 **Upcoming:**")
                for e in events:
                    days = (e.date - today_date).days
                    lines.append(f"  • {e.title} — {days} day{'s' if days != 1 else ''} away")

            # Motivational quote
            quote = random.choice(self.MOTIVATIONAL_QUOTES)
            lines.append(f"\n💪 _{quote}_")

            return {'response': '\n'.join(lines), 'data': {}, 'mode': 'general'}
        except Exception:
            return {'response': f"Good morning, {self.user.first_name}! Have a productive day! 💪", 'data': {}}


# ── Conversation Memory ────────────────────────────────────────────────────────

def update_user_memory(user, session):
    """Update persistent AI memory after a conversation session."""
    try:
        from apps.accounts.models import UserMemory
        from apps.students.models import Result

        memory, _ = UserMemory.objects.get_or_create(user=user)

        if user.is_student:
            profile = user.student_profile
            results = list(Result.objects.filter(student=profile).select_related('course').order_by('grade_points'))
            weak = [r.course.name for r in results if r.grade_points and float(r.grade_points) < 2.0][:3]
            strong = [r.course.name for r in reversed(results) if r.grade_points and float(r.grade_points) >= 3.5][:3]
            memory.weak_subjects = weak
            memory.strong_subjects = strong

            # Mood trend
            from apps.accounts.models import MoodCheckIn
            recent_moods = list(MoodCheckIn.objects.filter(user=user).order_by('-created_at')[:5].values_list('mood', flat=True))
            if len(recent_moods) >= 2:
                if recent_moods[0] > recent_moods[-1]:
                    memory.mood_trend = 'improving'
                elif recent_moods[0] < recent_moods[-1]:
                    memory.mood_trend = 'declining'
                else:
                    memory.mood_trend = 'stable'

            memory.summary = (
                f"Student {user.get_full_name()} ({user.user_id}), "
                f"Level {profile.level}, GPA {profile.cumulative_gpa}. "
                f"Weak: {', '.join(weak) or 'none'}. "
                f"Strong: {', '.join(strong) or 'none'}. "
                f"Streak: {user.study_streak} days. Points: {user.points}."
            )
            memory.save()
    except Exception:
        pass


def get_user_memory_context(user):
    """Get persistent memory to inject into system prompt."""
    try:
        from apps.accounts.models import UserMemory
        memory = UserMemory.objects.filter(user=user).first()
        if memory and memory.summary:
            return f"\nPERSISTENT MEMORY: {memory.summary}"
    except Exception:
        pass
    return ""

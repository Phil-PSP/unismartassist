"""
Student services - GPA analysis, document processing
"""
import pdfplumber
import PyPDF2
from .models import Result, GPARecord


class GPAAnalyzer:
    """Analyze student GPA and provide insights"""

    def __init__(self, student_profile):
        self.profile = student_profile

    def get_trend_data(self):
        records = GPARecord.objects.filter(student=self.profile).order_by('academic_year', 'semester')
        return [{'label': f"{r.academic_year} S{r.semester}", 'gpa': float(r.gpa)} for r in records]

    def get_performance_by_course(self):
        results = Result.objects.filter(student=self.profile).select_related('course')
        return [{'course': r.course.name, 'code': r.course.code,
                 'grade': r.grade, 'score': float(r.score or 0)} for r in results]

    def get_weak_subjects(self):
        """Courses with grade D or F"""
        results = Result.objects.filter(
            student=self.profile, grade__in=['D+', 'D', 'F']
        ).select_related('course')
        return [{'course': r.course.name, 'grade': r.grade} for r in results]

    def get_strong_subjects(self):
        """Courses with grade A or A+"""
        results = Result.objects.filter(
            student=self.profile, grade__in=['A+', 'A']
        ).select_related('course')
        return [{'course': r.course.name, 'grade': r.grade} for r in results]

    def get_improvement_tips(self):
        """Generate improvement tips based on GPA"""
        gpa = float(self.profile.cumulative_gpa)
        tips = []
        if gpa < 1.5:
            tips = [
                "Your GPA is critically low. Consider meeting your academic advisor immediately.",
                "Focus on your weakest subjects first.",
                "Form study groups with high-performing classmates.",
                "Visit the library daily and use past questions.",
            ]
        elif gpa < 2.5:
            tips = [
                "Your GPA needs improvement. Create a structured study schedule.",
                "Attend all lectures and take detailed notes.",
                "Practice past exam questions regularly.",
                "Seek help from lecturers during office hours.",
            ]
        elif gpa < 3.5:
            tips = [
                "Good progress! Push for a First Class by targeting weak subjects.",
                "Review your notes within 24 hours of each lecture.",
                "Use spaced repetition for memorization.",
            ]
        else:
            tips = [
                "Excellent GPA! Maintain your study habits.",
                "Consider mentoring other students.",
                "Explore research opportunities with lecturers.",
            ]
        return tips


class DocumentProcessor:
    """Process uploaded PDFs and extract content"""

    def __init__(self, document):
        self.document = document

    def extract_text(self):
        """Extract text from PDF"""
        text = ''
        try:
            with pdfplumber.open(self.document.file.path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ''
        except Exception:
            try:
                with open(self.document.file.path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() or ''
            except Exception as e:
                text = f"Could not extract text: {str(e)}"
        return text

    def summarize(self, text, max_sentences=5):
        """Simple extractive summarization"""
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 30]
        # Score sentences by keyword frequency
        words = text.lower().split()
        word_freq = {}
        for w in words:
            if len(w) > 4:
                word_freq[w] = word_freq.get(w, 0) + 1

        scored = []
        for s in sentences:
            score = sum(word_freq.get(w.lower(), 0) for w in s.split())
            scored.append((score, s))

        scored.sort(reverse=True)
        top = [s for _, s in scored[:max_sentences]]
        return '. '.join(top) + '.'

    def extract_key_points(self, text, max_points=8):
        """Extract key points (sentences with important keywords)"""
        keywords = ['important', 'key', 'note', 'remember', 'definition',
                    'formula', 'theorem', 'law', 'principle', 'concept']
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        key_points = []
        for s in sentences:
            if any(kw in s.lower() for kw in keywords):
                key_points.append(s)
            if len(key_points) >= max_points:
                break
        # If not enough keyword-based points, take first sentences
        if len(key_points) < 3:
            key_points = sentences[:max_points]
        return key_points[:max_points]

    def process(self):
        """Full processing pipeline"""
        text = self.extract_text()
        summary = self.summarize(text)
        key_points = self.extract_key_points(text)
        self.document.summary = summary
        self.document.key_points = key_points
        self.document.processed = True
        self.document.save(update_fields=['summary', 'key_points', 'processed'])
        return {'summary': summary, 'key_points': key_points}

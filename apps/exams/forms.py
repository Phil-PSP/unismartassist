"""
Forms for Exam Management
"""
from django import forms
from .models import Exam, Question, QuestionOption, PastQuestionFile
import csv
import json
from pathlib import Path


class BulkQuestionUploadForm(forms.Form):
    """Form for uploading questions in bulk via CSV or JSON"""
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all(),
        required=True,
        help_text="Select the exam to add questions to"
    )
    file = forms.FileField(
        required=True,
        help_text="Upload CSV or JSON file with questions"
    )
    file_format = forms.ChoiceField(
        choices=[('csv', 'CSV'), ('json', 'JSON')],
        initial='csv',
        help_text="File format"
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            if not file.name.endswith(('.csv', '.json')):
                raise forms.ValidationError("Only CSV and JSON files are allowed")
            
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 5MB")
            try:
                raw = file.read()
                text = raw.decode('utf-8-sig')
                extension = Path(file.name).suffix.lower()
                if extension == '.json':
                    payload = json.loads(text)
                    questions = payload.get('questions') if isinstance(payload, dict) else None
                    if not isinstance(questions, list) or not questions or len(questions) > 2000:
                        raise forms.ValidationError("JSON must contain 1 to 2000 questions in a 'questions' array.")
                    if any(not isinstance(item, dict) or not item.get('question_text') for item in questions):
                        raise forms.ValidationError("Each JSON question must be an object with question_text.")
                else:
                    reader = csv.DictReader(text.splitlines())
                    required = {'question_text'}
                    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                        raise forms.ValidationError("CSV must include a question_text column.")
                    rows = list(reader)
                    if not rows or len(rows) > 2000:
                        raise forms.ValidationError("CSV must contain 1 to 2000 question rows.")
            except forms.ValidationError:
                raise
            except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, TypeError):
                raise forms.ValidationError("The uploaded file is not valid UTF-8 CSV or JSON.")
            finally:
                file.seek(0)
        
        return file
    
    def clean(self):
        cleaned = super().clean()
        uploaded = cleaned.get('file')
        file_format = cleaned.get('file_format')
        if uploaded and file_format:
            extension = Path(uploaded.name).suffix.lower().lstrip('.')
            if extension != file_format:
                self.add_error('file_format', 'Selected format does not match the uploaded file.')
        return cleaned

    def process_csv(self, file, exam):
        """Process CSV file and create questions"""
        import io
        
        # Read CSV
        file_content = file.read().decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        questions_created = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Create question
                question = Question.objects.create(
                    exam=exam,
                    question_text=row['question_text'],
                    question_type=row.get('question_type', 'multiple_choice'),
                    marks=int(row.get('marks', 1)),
                    order=int(row.get('order', 0)),
                    expected_answer=row.get('expected_answer', '')
                )
                
                # Create options (for multiple choice and true/false)
                if question.question_type in ['multiple_choice', 'true_false']:
                    # Options should be in format: option1|option2|option3|option4
                    options_text = row.get('options', '').split('|')
                    # Correct answers should be in format: 0,2 (indices of correct options)
                    correct_indices = [int(i.strip()) for i in row.get('correct_answers', '0').split(',')]
                    
                    for idx, option_text in enumerate(options_text):
                        if option_text.strip():
                            QuestionOption.objects.create(
                                question=question,
                                option_text=option_text.strip(),
                                is_correct=(idx in correct_indices),
                                order=idx + 1
                            )
                
                questions_created += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return questions_created, errors
    
    def process_json(self, file, exam):
        """Process JSON file and create questions"""
        import json
        
        # Read JSON
        file_content = file.read().decode('utf-8')
        data = json.loads(file_content)
        
        questions_created = 0
        errors = []
        
        questions_data = data.get('questions', [])
        
        for idx, q_data in enumerate(questions_data, start=1):
            try:
                # Create question
                question = Question.objects.create(
                    exam=exam,
                    question_text=q_data['question_text'],
                    question_type=q_data.get('question_type', 'multiple_choice'),
                    marks=q_data.get('marks', 1),
                    order=q_data.get('order', idx),
                    expected_answer=q_data.get('expected_answer', '')
                )
                
                # Create options
                for opt_idx, opt_data in enumerate(q_data.get('options', []), 1):
                    QuestionOption.objects.create(
                        question=question,
                        option_text=opt_data['text'],
                        is_correct=opt_data.get('is_correct', False),
                        order=opt_idx
                    )
                
                questions_created += 1
                
            except Exception as e:
                errors.append(f"Question {idx}: {str(e)}")
        
        return questions_created, errors


class PastQuestionUploadForm(forms.ModelForm):
    """Form for uploading past question papers with basic content validation."""
    class Meta:
        model = PastQuestionFile
        fields = ['course', 'title', 'description', 'file', 'file_type', 
                  'academic_year', 'semester', 'exam_type']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_file(self):
        uploaded = self.cleaned_data.get('file')
        if not uploaded:
            return uploaded
        if uploaded.size > 15 * 1024 * 1024:
            raise forms.ValidationError('File size must not exceed 15 MB.')
        extension = Path(uploaded.name).suffix.lower()
        file_type = self.data.get('file_type')
        allowed = {
            'pdf': {'.pdf'},
            'image': {'.png', '.jpg', '.jpeg', '.webp'},
            'doc': {'.doc', '.docx'},
        }
        if extension not in allowed.get(file_type, set()):
            raise forms.ValidationError('The file extension does not match the selected file type.')
        header = uploaded.read(16)
        uploaded.seek(0)
        valid = False
        if file_type == 'pdf':
            valid = header.startswith(b'%PDF-')
        elif file_type == 'image':
            valid = (
                header.startswith(b'\x89PNG\r\n\x1a\n')
                or header.startswith(b'\xff\xd8\xff')
                or (header.startswith(b'RIFF') and header[8:12] == b'WEBP')
            )
        elif file_type == 'doc':
            valid = header.startswith(b'PK\x03\x04') or header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1')
        if not valid:
            raise forms.ValidationError('The file content does not match the selected file type.')
        return uploaded

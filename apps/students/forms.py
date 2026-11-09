from django import forms
from pathlib import Path
from .models import Document, CourseRegistration


class DocumentUploadForm(forms.ModelForm):
    MAX_FILE_SIZE = 10 * 1024 * 1024

    class Meta:
        model = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Document title'}),
            'file': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx,.txt'}),
        }

    def clean_file(self):
        uploaded = self.cleaned_data.get('file')
        if not uploaded:
            return uploaded
        extension = Path(uploaded.name).suffix.lower()
        if extension not in {'.pdf', '.doc', '.docx', '.txt'}:
            raise forms.ValidationError('Only PDF, DOC, DOCX and TXT files are allowed.')
        if uploaded.size > self.MAX_FILE_SIZE:
            raise forms.ValidationError('Document size must not exceed 10 MB.')
        header = uploaded.read(16)
        uploaded.seek(0)
        valid = (
            (extension == '.pdf' and header.startswith(b'%PDF-'))
            or (extension == '.docx' and header.startswith(b'PK\x03\x04'))
            or (extension == '.doc' and header.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'))
            or (extension == '.txt' and self._is_utf8_text(uploaded))
        )
        if not valid:
            raise forms.ValidationError('The file content does not match its extension.')
        return uploaded

    @staticmethod
    def _is_utf8_text(uploaded):
        try:
            for chunk in uploaded.chunks():
                chunk.decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False
        finally:
            uploaded.seek(0)


class CourseRegistrationForm(forms.Form):
    courses = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    def __init__(self, *args, level=None, semester=None, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Course
        qs = Course.objects.all()
        if level:
            qs = qs.filter(level=level)
        if semester:
            qs = qs.filter(semester=semester)
        self.fields['courses'].queryset = qs

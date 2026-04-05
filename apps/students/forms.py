from django import forms
from .models import Document, CourseRegistration


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Document title'}),
            'file': forms.FileInput(attrs={'class': 'form-input', 'accept': '.pdf,.doc,.docx,.txt'}),
        }


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

from django import forms
from .models import Class, Assignment

class UploadFileForm(forms.Form):
    file = forms.FileField()

class AddStudentForm(forms.Form):
    user_id = forms.IntegerField(label="Student User ID")
    class_id = forms.ModelChoiceField(queryset=Class.objects.all(), label="Class")

class CreateClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['code', 'name']

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['name', 'deadline', 'role']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

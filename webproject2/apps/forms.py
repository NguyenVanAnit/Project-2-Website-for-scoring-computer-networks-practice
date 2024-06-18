from django import forms
from .models import Class, Assignment
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

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

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    error_messages = {
        'invalid_login': 'Tên đăng nhập hoặc mật khẩu không chính xác. Vui lòng thử lại.',  # Thông báo lỗi tùy chỉnh
        'inactive': 'Tài khoản này đã bị vô hiệu hóa.',
    }

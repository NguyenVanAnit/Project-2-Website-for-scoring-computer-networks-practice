from django import forms
from .models import Class, Assignment
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .utils import text_to_hex


class UploadFileForm(forms.Form):
    file = forms.FileField()

class AddStudentForm(forms.Form):
    user_id = forms.CharField(
        required=False,  # Cho phép trống vì có thể dùng file CSV
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập ID sinh viên'
        })
    )

class CreateClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['code', 'name']

class AssignmentForm(forms.ModelForm):
    title = forms.CharField(max_length=200, required=True)

    def clean_title(self):
        title = self.cleaned_data['title']
        return text_to_hex(title)
    class Meta:
        model = Assignment
        fields = ['name', 'deadline', 'role', 'title']
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

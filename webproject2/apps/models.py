from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Class(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classes_taught', limit_choices_to={'role': 1})
    students = models.ManyToManyField(User, related_name='classes_enrolled', limit_choices_to={'role': 0})

    def __str__(self):
        return self.name


class Assignment(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='assignments')
    name = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    ROLE_CHOICES_A = (
        (0, 'Bài thực hành 4'),
        (1, 'Bài thực hành 5'),
    )
    role = models.IntegerField(choices=ROLE_CHOICES_A, default=0)

    def __str__(self):
        return self.name

class Submission(models.Model):
    assignment_id = models.ForeignKey('Assignment', on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    submission_time = models.DateTimeField(auto_now_add=True)
    is_submited = models.BooleanField(default=False)
    # Thêm trường cho nội dung nộp bài, đánh giá, v.v.
    
    

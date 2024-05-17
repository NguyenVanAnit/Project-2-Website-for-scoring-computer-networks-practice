from django.contrib import admin
from .models import Class, Assignment, Submission

# Register your models here.
admin.site.register(Class)
admin.site.register(Assignment)
admin.site.register(Submission)

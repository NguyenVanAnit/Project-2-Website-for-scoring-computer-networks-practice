from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # path('login/', views.Login.as_view(), name='login'),
    path('home-teacher/', views.teacher_home, name='home-teacher'),
    path('submitEx4/<int:assignment_id>/', views.submitEx4.as_view(), name='ex4'),
    path('upload/<int:assignment_id>/', views.upload_pcap, name='upload'),
    path('add-student/', views.addStudenToClass, name="add-student"),
    path('list-classes/', views.list_classes, name='list-classes'),
    path('creat-class/', views.create_class, name="create-class"),
    path('class/<int:class_id>/', views.class_detail, name='class_detail'),
    path('logout/', views.custom_logout, name='logout'),
    path('login/', views.custom_login, name='login'),
    path('', views.home, name='home'),
    path('student-home/', views.student_home, name='home-student'),
    path('student-classes/', views.student_classes, name='student_classes'),
    path('student_class_detail/<int:class_id>/', views.student_class_detail, name='student_class_detail'),
    path('assignment/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('student/<int:student_id>/submissions/', views.student_submission_detail, name='student_submission_detail'),
    path('view_assignment_submissions/<int:assignment_id>/', views.view_assignment_submissions, name='view_assignment_submissions'),
    path('student/<int:student_id>/assignments/', views.view_student_assignments, name='view_student_assignments'),
    path('class/<int:class_id>/delete_student/', views.delete_student_from_class, name='delete_student_from_class'),
    path('submission/<int:submission_id>/', views.view_student_submission, name='view_student_submission'),
    path('class/<int:class_id>/delete/', views.delete_class_for_student, name='delete_class_for_student'),
    # path('view_result/<int:assignment_id>/', views.view_result, name='view_result'),
    path('view_result/<int:assignment_id>/', views.ViewResult.as_view(), name='view_result'),
    path('submitEx5/<int:assignment_id>/', views.submitEx5.as_view(), name='ex5'),



    # path('list-class/teacherid=<int:user_id>', view.)
]
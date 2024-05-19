from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.Login.as_view(), name='login'),
    path('home-teacher/', views.get_home_teacher, name='home-teacher'),
    path('submitEx4/', views.submitEx4.as_view(), name='ex4'),
    path('upload/', views.upload_pcap.as_view(), name='upload'),
    # path('list-class/teacherid=<int:user_id>', view.)
]
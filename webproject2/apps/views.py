from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
import json
import os

# Create your views here.
class Login(View):
    def get(self, request):
        return render(request, 'apps/login.html')
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)
        user = authenticate(username=username, password=password)
        
        if user is None:
            return HttpResponse('Tài khoản không tồn tại')
        
        login(request, user)
        
        if user.role == 0:
            return HttpResponse('Trang chủ học sinh')
        elif user.role == 1:
            return render(request, 'apps/teacher/home.html', {'user': user})
        elif user.role == 2:
            return HttpResponse('Admin')
        else:
            return HttpResponse('Lỗi role')
        
def get_home_teacher(request):
    return render(request, 'apps/teacher/home.html')

class submitEx4(View):
    def get(self, request):
        return render(request, 'apps/student/ex4.html')
    
    def post(self, request):

        stt = request.POST.get('stt')
        souIP = request.POST.get('souIP')
        desIP = request.POST.get('desIP')
        souPort = request.POST.get('souPort')
        desPort = request.POST.get('desPort')
        floor = request.POST.get('floor')

        stt2 = request.POST.get('stt2')
        reason2 = request.POST.get('reason2')
        success2 = request.POST.get('success2')
        reason22 = request.POST.get('reason22')

        data = {
            'c1':{
                'stt': stt,
                'souIP': souIP,
                'desIP': desIP,
                'souPort': souPort,
                'desPort': desPort,
                'floor': floor
            },
            'c2':{
                'stt2': stt2,
                'reason2': reason2,
                'success2': success2,
                'reason22': reason22
            }
        }

        with open('data.json', 'w') as json_file:
            json.dump(data, json_file)

        with open('data.json') as f:
            d = json.load(f)

        a = d['c1']['souPort']
        print(a)
        
        return HttpResponse("Data saved to JSON file")





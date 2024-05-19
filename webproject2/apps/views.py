from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
import json
import os
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from scapy.all import rdpcap
from django.conf import settings

from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP

from .forms import UploadFileForm

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

class upload_pcap(View):
    def get(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        return render(request, 'apps/student/upload_pcap.html', {'form': form})
    
    def post(self, request):
        pcap_file = request.FILES['file']
        if not pcap_file:
            return HttpResponse("No file uploaded")        
        file_path = default_storage.save(pcap_file.name, pcap_file)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        # Đọc file PCAP và chuyển thành JSON
        packets = rdpcap(full_path)
        data_list = []
        for packet in packets:
            packet_dict = packet.fields
            data_list.append(packet_dict)
        
        json_file_path = os.path.join(settings.BASE_DIR, 'data', 'pcap_data.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(data_list, json_file)

        return HttpResponse('Successful')
        

# @csrf_exempt
# def upload_pcap(request):
#     if request.method == 'POST':
#         if 'pcap_file' not in request.FILES:
#             print("No file found in request.FILES")
#             return HttpResponse("No file uploaded")
        
#         print("File found in request.FILES")
#         pcap_file = request.FILES['pcap_file']
#         print(f"Uploaded file name: {pcap_file.name}")
        
#         file_path = default_storage.save(pcap_file.name, pcap_file)
#         full_path = os.path.join(settings.MEDIA_ROOT, file_path)
#         print(f"Saved file path: {full_path}")

#         # Đọc file PCAP và chuyển thành JSON
#         packets = rdpcap(full_path)
#         data_list = []
#         for packet in packets:
#             packet_dict = packet.fields
#             data_list.append(packet_dict)

#         json_file_path = os.path.join(settings.DATA_DIR, 'pcap_data.json')
#         with open(json_file_path, 'w') as json_file:
#             json.dump(data_list, json_file)

#         return HttpResponse(f"Data saved to JSON file at {json_file_path}")
#     else:
#         return HttpResponse("Invalid request")

# def pcap(request):
#     return render(request, 'apps/student/upload_pcap.html')
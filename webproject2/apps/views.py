from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
import json
import os
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from scapy.all import rdpcap
from django.conf import settings

from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP, UDP

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

class submitEx4(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):
        return render(request, 'apps/student/ex4.html')
    
    def post(self, request):

        # c1
        stt = request.POST.get('stt')
        souIP = request.POST.get('souIP')
        desIP = request.POST.get('desIP')
        souPort = request.POST.get('souPort')
        desPort = request.POST.get('desPort')
        floor = request.POST.get('floor')

        # c2
        stt2 = request.POST.get('stt2')
        reason2 = request.POST.get('reason2')
        success2 = request.POST.get('success2')
        reason22 = request.POST.get('reason22')

        # c4
        stt4 = request.POST.get('stt4')
        souIP4 = request.POST.get('souIP3')
        desIP4 = request.POST.get('desIP3')
        souPort4 = request.POST.get('souPort3')
        desPort4 = request.POST.get('desPort3')
        seq4 = request.POST.get('seq4')
        ack4 = request.POST.get('ack4')
        lenghttcp4 = request.POST.get('lenghttcp4')
        lenghtdata4 = request.POST.get('lenghtdata4')
        flag4 = request.POST.get('flag4')
        floor4 = request.POST.get('floor4')

        # data = {
        #     'c1':{
        #         'stt': stt,
        #         'souIP': souIP,
        #         'desIP': desIP,
        #         'souPort': souPort,
        #         'desPort': desPort,
        #         'floor': floor
        #     },
        #     'c2':{
        #         'stt2': stt2,
        #         'reason2': reason2,
        #         'success2': success2,
        #         'reason22': reason22
        #     }
        # }

        # with open('data.json', 'w') as json_file:
        #     json.dump(data, json_file)

        # with open('data.json') as f:
        #     d = json.load(f)

        # a = d['c1']['souPort']
        # print(a)
        
        # return HttpResponse("Data saved to JSON file")
        # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        # json_file_path = os.path.join(settings.BASE_DIR, 'data', 'pcap_data.json')

        # Đọc dữ liệu từ file JSON
        with open('data/pcap_data.json', 'r') as json_file:
            packets = json.load(json_file)

        score = 0
        for packet in packets:
            j_stt = packet.get('stt')
            j_src_ip = packet.get('src_ip')
            j_dst_ip = packet.get('dst_ip')
            j_src_port = packet.get('src_port')
            j_dst_port = packet.get('dst_port')
            j_protocol = packet.get('protocol')
            j_payload = packet.get('payload')
            j_payload = str(j_payload)
            j_seq = packet.get('seq')
            j_ack = packet.get('ack')
            j_lenght_payload = packet.get('lenght_payload')
            
            # c1, c2
            if int(stt) == j_stt and j_protocol == 'UDP':
                # c1
                if souIP == j_src_ip:
                    score += 0.25
                if desIP == j_dst_ip:
                    score += 0.25
                if int(souPort) == j_src_port:
                    score += 0.25
                if int(desPort) == j_dst_port:
                    score += 0.25
                if floor is not None:
                    if int(floor) == 4:
                        score += 0.25

                # c2
                start_stt = int(stt)
                dst_packet_c1_stt = 0
                for dst_packet in packets:
                    if int(dst_packet.get('stt')) < int(stt):
                        continue
                    if j_src_ip == dst_packet.get('dst_ip') and j_dst_ip == dst_packet.get('src_ip') and dst_packet.get('protocol') == 'UDP':
                        dst_packet_c1_stt = dst_packet.get('stt')
                        break
                if int(stt2) == int(dst_packet_c1_stt):
                    score += 0.25
                if success2 is not None:
                    if int(success2) == 0:
                        score += 0.25
                print('c1, c2')

            # c4
            start_stt4 = 9999999
            if j_protocol == 'TCP' and j_dst_ip == '202.191.56.66':
                strpayload = "414c49434527532041" # ALICE'S A
                if strpayload in j_payload:
                    if int(stt4) == j_stt:
                        score += 0.25
                    if souIP4 == j_src_ip:    
                        score += 0.25
                    if desIP4 == '202.191.56.66':
                        score += 0.25
                    if int(souPort4) == j_src_port:
                        score += 0.25
                    if int(desPort4) == j_dst_port:
                        score += 0.25
                    if int(seq4) == j_seq:
                        score += 0.25
                    if ack4 == 1:
                        score += 0.25
                    if int(lenghttcp4) == 20:
                        score += 0.25
                    if int(lenghtdata4) == j_lenght_payload:
                        score += 0.25
                    if flag4 == 'ACK':
                        score += 0.25
                    if floor4 is not None:
                        if int(floor4) == 4:
                            score += 0.25
                    print('c4')
                    start_stt4 = j_stt
                    print(start_stt4)

            # c5
            start_stt5 = True
            if j_stt > start_stt4 and start_stt5:
                print(1)
                if j_dst_ip == '202.191.56.66' and j_protocol == 'TCP':
                    start_stt5 = False
                    print(j_stt)




        return HttpResponse(score)

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
        # packets = rdpcap(full_path)
        # data_list = []
        # for packet in packets:
        #     packet_dict = packet.fields
        #     data_list.append(packet_dict)

        packets = RawPcapReader(full_path)
        data_list = []
        count = 0

        port1 = None
        port2 = None
        client_sequence_offset = None
        server_sequence_offset = None

        for (pkt_data, pkt_metadata,) in packets:
            count += 1

            ether_pkt = Ether(pkt_data)
        
            # bỏ qua những frame LLC(Logical Link Control) vì những frame này không có trường type như các gói thông thường
            if 'type' not in ether_pkt.fields:
                continue

            # kiểm tra xem gói nào không phải IPv4, 0x0800 là mã định danh của giao thức IPv4
            if ether_pkt.type != 0x0800:
                continue

            # giúp truy cập và lưu trữ gói tin IP bên trong gói Ethernet vào một biến mới là ip_pkt
            ip_pkt = ether_pkt[IP]
            # truy cập trường proto trong gói IP, proto == 6 đại diện cho gói tin TCP
            if ip_pkt.proto == 6:
                # giúp truy cập và lưu trữ gói tin TCP bên trong gói IP và lưu vào biến mới là tcp_pkt
                tcp_pkt = ip_pkt[TCP]
                tcp_payload = bytes(tcp_pkt.payload) if len(tcp_pkt.payload) > 0 else None
                
                if ip_pkt.dst == '202.191.56.66':
                    if port1 == None:
                        port1 = tcp_pkt.sport
                    elif port1 != tcp_pkt.sport:
                        port2 = tcp_pkt.sport

                if ip_pkt.dst == '202.191.56.66' and port2 == tcp_pkt.sport:
                    if client_sequence_offset == None:
                        client_sequence_offset = tcp_pkt.seq
                    relative_sequence_offset = tcp_pkt.seq - client_sequence_offset
                elif ip_pkt.src == '202.191.56.66' and port2 == tcp_pkt.dport:
                    if server_sequence_offset == None:
                        server_sequence_offset = tcp_pkt.seq
                    relative_sequence_offset = tcp_pkt.seq - server_sequence_offset
                else:
                    relative_sequence_offset = -1
                
                # print(count)
                # print(tcp_pkt.ack)
                if ('A' not in str(tcp_pkt.flags)):
                    relative_offset_ack = -2
                else:
                    if ip_pkt.dst == '202.191.56.66' and port2 == tcp_pkt.sport:
                        relative_offset_ack = tcp_pkt.ack - client_sequence_offset
                        # print(client_sequence_offset)
                    elif ip_pkt.src == '202.191.56.66' and port2 == tcp_pkt.dport:
                        relative_offset_ack = tcp_pkt.ack - server_sequence_offset
                        # print(server_sequence_offset)
                    else:
                        relative_offset_ack = -1
                
                # # Kích thước tổng của gói tin
                # total_length = len(pkt_data)
                
                # # Kích thước phần header
                # header_length = 0
                
                # # Tính kích thước Ethernet header (nếu có)
                # if ether_pkt.haslayer(Ether):
                #     header_length += len(ether_pkt[Ether])
                
                # # Tính kích thước IP header (nếu có)
                # if ether_pkt.haslayer(IP):
                #     header_length += len(ether_pkt[IP])
                
                # # Tính kích thước TCP/UDP header (nếu có)
                # if ether_pkt.haslayer(TCP):
                #     header_length += len(ether_pkt[TCP])
                # elif ether_pkt.haslayer(UDP):
                #     header_length += len(ether_pkt[UDP])
                
                # # Kích thước phần dữ liệu (payload)
                # payload_length = total_length - header_length
                

                packet_info = {
                    'stt': count,
                    'src_ip': ip_pkt.src,
                    'dst_ip': ip_pkt.dst,
                    'src_port': tcp_pkt.sport,
                    'dst_port': tcp_pkt.dport,
                    'protocol': 'TCP',
                    'payload': tcp_payload.hex() if tcp_payload else None,
                    'seq': relative_sequence_offset,
                    'ack': relative_offset_ack,
                    'lenght_payload': len(tcp_pkt.payload)
                }
            elif ip_pkt.proto == 17:
                tcp_pkt = ip_pkt[UDP]
                packet_info = {
                    'stt': count,
                    'src_ip': ip_pkt.src,
                    'dst_ip': ip_pkt.dst,
                    'src_port': tcp_pkt.sport,
                    'dst_port': tcp_pkt.dport,
                    'protocol': 'UDP',
                    'payload': 'null',
                    'seq': -1,
                    'ack': -3,
                    'lenght_payload': 0
                }     
            else:
                continue
            
            data_list.append(packet_info)
        
        json_file_path = os.path.join(settings.BASE_DIR, 'data', 'pcap_data.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(data_list, json_file)

        return render(request, 'apps/student/ex4.html')
    
        

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
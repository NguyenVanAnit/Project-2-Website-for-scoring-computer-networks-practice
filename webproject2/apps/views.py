from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, decorators
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

from .models import Class, Assignment, Submission
from .forms import AddStudentForm, CreateClassForm, AssignmentForm
from django.contrib import messages

from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomAuthenticationForm

from django.utils import timezone

from django.contrib.auth import logout

import binascii
import time


# Create your views here.
def home(request):
    return render(request, 'apps/home.html')

def custom_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.role == 1:  # Teacher
                    return redirect('home-teacher')
                elif user.role == 0:  # Student
                    return redirect('home-student')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'apps/login.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('login')

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
            classes = request.user.classes_enrolled.all()
            return render(request, 'apps/student/home.html', {'user': user, 'classes': classes})
        elif user.role == 1:
            classes = request.user.classes_taught.all()
            return render(request, 'apps/teacher/home.html', {'user': user, 'classes': classes})
        elif user.role == 2:
            return HttpResponse('')
        else:
            return HttpResponse('Lỗi role')
        
def get_home_teacher(request):
    return render(request, 'apps/teacher/home.html')

def teacher_home(request):
    if request.user.role != 1:  # Check if the user is not a teacher
        return redirect('home')  # Redirect to a suitable page if the user is not a teacher
    return render(request, 'apps/teacher/home.html')

def student_home(request):
    if request.user.role != 0:  # Check if the user is not a teacher
        return redirect('home')  # Redirect to a suitable page if the user is not a teacher
    return render(request, 'apps/student/home.html')

@decorators.login_required(login_url = '/login/')
def list_classes(request):
    if request.user.role != 1:  # Ensure the user is a teacher
        return redirect('home')
    
    classes = request.user.classes_taught.all()
    return render(request, 'apps/teacher/list-classes.html', {'classes': classes})

@decorators.login_required(login_url = '/login/')
def create_class(request):
    if request.user.role != 1:  # Ensure the user is a teacher
        return redirect('home')
    
    if request.method == 'POST':
        form = CreateClassForm(request.POST)
        if form.is_valid():
            new_class = form.save(commit=False)
            new_class.teacher = request.user
            new_class.save()
            messages.success(request, 'Class created successfully!')
            return redirect('list-classes')
    else:
        form = CreateClassForm()
    
    return render(request, 'apps/teacher/create-class.html', {'form': form})

@decorators.login_required(login_url = '/login/')
def class_detail(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id, teacher=request.user)
    assignments = Assignment.objects.filter(class_id=class_instance)
    form = None
    form2 = None
    
    if request.method == 'POST':
        if 'add_student' in request.POST:
            form = AddStudentForm(request.POST)
            if form.is_valid():
                user_id = form.cleaned_data['user_id']
                try:
                    student = User.objects.get(user_id=user_id)
                    if student.role != 0:
                        messages.error(request, 'The user is not a student.')
                    else:
                        class_instance.students.add(student)
                        messages.success(request, f'Student {student.username} added to class {class_instance.name}.')
                except User.DoesNotExist:
                    messages.error(request, 'Student with the given User ID does not exist.')
            return redirect('class_detail', class_id=class_instance.id)
        elif 'add_assignment' in request.POST:
            form2 = AssignmentForm(request.POST)
            if form2.is_valid():
                assignment = form2.save(commit=False)
                assignment.class_id = class_instance
                assignment.save()
                messages.success(request, f'Assignment {assignment.name} added to class {class_instance.name}.')
            return redirect('class_detail', class_id=class_instance.id)
    else:
        form = AddStudentForm()
        form2 = AssignmentForm()

    students = class_instance.students.all()
    return render(request, 'apps/teacher/class_detail.html', {
        'class_instance': class_instance,
        'students': students,
        'form': form,
        'form2': form2,
        'assignments': assignments
    })

# def class_detail(request, class_id):
#     class_instance = get_object_or_404(Class, id=class_id, teacher=request.user)
#     assignments = Assignment.objects.filter(class_id=class_instance)
#     form = AddStudentForm()  # Form thêm học sinh
#     form2 = AssignmentForm()  # Form thêm bài tập mới

#     if request.method == 'POST':
#         if 'add_student' in request.POST:
#             form = AddStudentForm(request.POST)
#             if form.is_valid():
#                 user_id = form.cleaned_data['user_id']
#                 try:
#                     student = User.objects.get(user_id=user_id)
#                     if student.role != 0:
#                         messages.error(request, 'The user is not a student.')
#                     else:
#                         class_instance.students.add(student)
#                         messages.success(request, f'Student {student.username} added to class {class_instance.name}.')
#                 except User.DoesNotExist:
#                     messages.error(request, 'Student with the given User ID does not exist.')
#         elif 'add_assignment' in request.POST:
#             form2 = AssignmentForm(request.POST)
#             if form2.is_valid():
#                 assignment = form2.save(commit=False)
#                 assignment.class_id = class_instance
#                 assignment.save()
#                 messages.success(request, f'Assignment {assignment.name} added to class {class_instance.name}.')

#     students = class_instance.students.all()
#     return render(request, 'apps/teacher/class_detail.html', {
#         'class_instance': class_instance,
#         'students': students,
#         'form': form,
#         'form2': form2,
#         'assignments': assignments
#     })

def view_student_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    assignment = submission.assignment
    now = timezone.now()
    show_score = now > assignment.deadline

    return render(request, 'apps/teacher/view_student_submission.html', {
        'assignment': assignment,
        'submission': submission,
        'show_score': show_score
    })


def view_assignment_submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = Submission.objects.filter(assignment_id=assignment)

    return render(request, 'apps/teacher/assignment_submissions.html', {'assignment': assignment, 'submissions': submissions})

def view_student_assignments(request, user_id):
    student = get_object_or_404(User, id=student_id)
    if request.user != student:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')

    assignments = Assignment.objects.filter(class_id__students=student)

    assignment_results = []
    for assignment in assignments:
        submission = Submission.objects.filter(assignment_id=assignment, student=student).first()
        if submission:
            result = {
                'assignment': assignment,
                'submission': submission,
                'show_score': timezone.now() > assignment.deadline
            }
            assignment_results.append(result)
        else:
            assignment_results.append({'assignment': assignment, 'submission': None, 'show_score': False})

    return render(request, 'apps/student/student_assignments.html', {'student': student, 'assignment_results': assignment_results})
# def class_detail(request, class_id):
#     class_instance = get_object_or_404(Class, id=class_id, teacher=request.user)

#     class_obj = get_object_or_404(Class, id=class_id)
#     assignments = Assignment.objects.filter(class_id=class_obj)

#     if request.method == 'POST':
#         form = AddStudentForm(request.POST)
#         form2 = AssignmentForm(request.POST)
#         if form.is_valid():
#             user_id = form.cleaned_data['user_id']
#             assignment = form.save(commit=False)
#             assignment.class_id = class_obj
#             assignment.save()
#             try:
#                 student = User.objects.get(user_id=user_id)
#                 if student.role != 0:
#                     messages.error(request, 'The user is not a student.')
#                 else:
#                     class_instance.students.add(student)
#                     messages.success(request, f'Student {student.username} added to class {class_instance.name}.')
#             except User.DoesNotExist:
#                 messages.error(request, 'Student with the given User ID does not exist.')
#             return redirect('class_detail', class_id=class_instance.id)
#     else:
#         form = AddStudentForm()
#         form2 = AssignmentForm()
    
#     students = class_instance.students.all()
#     return render(request, 'apps/teacher/class_detail.html', {'class_instance': class_instance, 'students': students, 'form': form, 'form2': form2, 'assignments': assignments})

def student_submission_detail(request, student_id):
    student = get_object_or_404(User, id=student_id)
    submissions = Submission.objects.filter(student=student)
    return render(request, 'apps/teacher/student_submission_detail.html', {'student': student, 'submissions': submissions})



def student_classes(request):
    if request.user.role != 0:  # Ensure the user is a student
        return redirect('home')
    classes = request.user.classes_enrolled.all()
    return render(request, 'apps/student/student_classes.html', {'classes': classes})

# def student_class_detail(request, class_id):
#     student = request.user
#     class_obj = get_object_or_404(Class, id=class_id, students=student)
#     assignments = Assignment.objects.filter(class_id=class_obj)
#     submissions = {}
#     for assignment in assignments:
#         submission = assignment.submissions.filter(student=student).first()
#         if submission:
#             submissions[assignment.id] = submission
#     return render(request, 'apps/student/class_detail.html', {'class_obj': class_obj, 'assignments': assignments, 'submissions': submissions})

def student_class_detail(request, class_id):
    student = request.user
    class_obj = get_object_or_404(Class, id=class_id, students=student)
    assignments = Assignment.objects.filter(class_id=class_obj)
    submissions = {}
    for assignment in assignments:
        submission = assignment.submissions.filter(student=student).first()
        if submission:
            submissions[assignment.id] = submission
    return render(request, 'apps/student/class_detail.html', {
        'class_obj': class_obj,
        'assignments': assignments,
        'submissions': submissions
    })

def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submission = Submission.objects.filter(assignment_id=assignment, student=request.user).first()
    can_view_score = submission.is_submited if submission else False  # Assuming is_submited is True when the score is available

    return render(request, 'apps/student/assignment_detail.html', {
        'assignment': assignment,
        'submission': submission,
        'can_view_score': can_view_score
    })

def view_result(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = request.user
    submission = get_object_or_404(Submission, assignment_id=assignment, student=student)

    # Kiểm tra nếu deadline đã qua
    is_past_deadline = assignment.deadline < timezone.now()

    return render(request, 'apps/student/view_result.html', {
        'submission': submission,
        'assignment': assignment,
        'is_past_deadline': is_past_deadline,
    })

def addStudenToClass(request):
    if request.method == 'POST':
        form = AddStudentForm(request.POST)
        if form.is_valid:
            user_id = form.cleaned_data['user_id']
            class_instance = form.cleaned_data['class_id']

            try:
                student = User.objects.get(user_id=user_id)
                if student.role != 0:
                    messages.error(request, 'The user is not a student.')
                else:
                    class_instance.students.add(student)
                    messages.success(request, f'Student {student.username} added to class {class_instance.name}.')
            except User.DoesNotExist:
                messages.error(request, 'Student with the given User ID does not exist.')

            return redirect('add_student_to_class')

    else:
        form = AddStudentForm()
        
    return render(request, 'apps/teacher/add-student-to-class.html', {'form': form})

def delete_student_from_class(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id, teacher=request.user)
    student_id = request.GET.get('student_id')
    if student_id:
        try:
            student = User.objects.get(id=student_id)
            if student in class_instance.students.all():
                class_instance.students.remove(student)
                messages.success(request, f'Học sinh {student.username} đã bị xóa khỏi lớp {class_instance.name}.')
            else:
                messages.error(request, 'Học sinh này không thuộc lớp.')
        except User.DoesNotExist:
            messages.error(request, 'Học sinh không tồn tại.')
    else:
        messages.error(request, 'Không tìm thấy học sinh để xóa.')

    return redirect('class_detail', class_id=class_instance.id)


class submitEx4(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request, assignment_id):
        assignment = get_object_or_404(Assignment, id=assignment_id)
        return render(request, 'apps/student/ex4.html', {'assignment': assignment})
    
    def post(self, request, assignment_id):
        assignment = get_object_or_404(Assignment, id=assignment_id)

        student = request.user

        current_time = timezone.now()
        # Kiểm tra deadline
        if current_time > assignment.deadline:
            return HttpResponse("The deadline for this assignment has passed.")
        
        # Kiểm tra xem học sinh đã nộp bài này chưa
        # submission = Submission.objects.filter(assignment_id=assignment, student=student).first()
        # if submission and submission.is_submited:
        #     return HttpResponse("You have already submitted this assignment.")
        
        answers = {
            'stt': request.POST.get('stt', ''),
            'souIP': request.POST.get('souIP', ''),
            'desIP': request.POST.get('desIP', ''),
            'souPort': request.POST.get('souPort', ''),
            'desPort': request.POST.get('desPort', ''),
            'floor': request.POST.get('floor', '')
        }

        # c1
        stt = request.POST.get('stt')
        souIP = request.POST.get('souIP')
        desIP = request.POST.get('desIP')
        souPort = request.POST.get('souPort')
        desPort = request.POST.get('desPort')
        floor = request.POST.get('floor')


        if stt == '':
            stt = -1
        if souPort == '':
            souPort = -1
        if desPort == '':
            desPort = -1
        if floor is None:
            floor = -1

        # c2
        stt2 = request.POST.get('stt2')
        reason2 = request.POST.get('reason21')
        success2 = request.POST.get('success2')
        reason22 = request.POST.get('reason22')

        if stt2 == '':
            stt2 = -1
        if success2 is None:
            success2 = -1

        # c4
        stt4 = request.POST.get('stt4')
        souIP4 = request.POST.get('souIP4')
        desIP4 = request.POST.get('desIP4')
        souPort4 = request.POST.get('souPort4')
        desPort4 = request.POST.get('desPort4')
        seq4 = request.POST.get('seq4')
        ack4 = request.POST.get('ack4')
        lenghttcp4 = request.POST.get('lenghttcp4')
        lenghtdata4 = request.POST.get('lenghtdata4')
        flag4 = request.POST.get('flag4')
        floor4 = request.POST.get('floor4')

        if stt4 == '':
            stt4 = -1
        if souPort4 == '':
            souPort4 = -1
        if desPort4 == '':
            desPort4 = -1
        if seq4 == '':
            seq4 = -1
        if ack4 == '':
            ack4 = -1
        if lenghttcp4 == '':
            lenghttcp4 = -1
        if lenghtdata4 == '':
            lenghtdata4 = -1
        if floor4 is None:
            floor4 = -1

        # c5
        stt5 = request.POST.get('stt5')
        souIP5 = request.POST.get('souIP5')
        desIP5 = request.POST.get('desIP5')
        souPort5 = request.POST.get('souPort5')
        desPort5 = request.POST.get('desPort5')
        seq5 = request.POST.get('seq5')
        ack5 = request.POST.get('ack5')
        lenghttcp5 = request.POST.get('lenghttcp5')
        lenghtdata5 = request.POST.get('lenghtdata5')
        flag5 = request.POST.get('flag5')
        success5 = request.POST.get('success5')

        if stt5 == '':
            stt5 = -1
        if souPort5 == '':
            souPort5 = -1
        if desPort5 == '':
            desPort5 = -1
        if seq5 == '':
            seq5 = -1
        if ack5 == '':
            ack5 = -1
        if lenghttcp5 == '':
            lenghttcp5 = -1
        if lenghtdata5 == '':
            lenghtdata5 = -1
        if success5 is None:
            success5 = -1

        # c6
        seq6 = request.POST.get('seq6')

        if seq6 == '':
            seq6 = -1

        #c7
        stt7 = request.POST.get('stt7')
        nhiphan7 = request.POST.get('nhiphan7')
        flag7 = request.POST.get('flag7')
        seq7 = request.POST.get('seq7')
        ack7 = request.POST.get('ack7')
        lenghtdata7 = request.POST.get('lenghtdata7')

        if stt7 == '':
            stt7 = -1
        if seq7 == '':
            seq7 = -1
        if ack7 == '':
            ack7 = -1
        if lenghtdata7 == '':
            lenghtdata7 = -1

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
        start_stt4 = 99999999
        start_stt5 = True
        start_ack5 = -98989898
        start_stt6 = True
        start_stt7 = True

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
            j_fin = packet.get('fin')
            
            # c1, c2  
            if int(stt) == j_stt and j_protocol == 'UDP':
                # c1
                if souIP == j_src_ip:
                    score += 1
                if desIP == j_dst_ip:
                    score += 1
                if int(souPort) == j_src_port:
                    score += 1
                if int(desPort) == j_dst_port:
                    score += 1
                if int(floor) == 4:
                    score += 1

                # c2
                dst_packet_c1_stt = 0
                for dst_packet in packets:
                    if int(dst_packet.get('stt')) < int(stt):
                        continue
                    if j_src_ip == dst_packet.get('dst_ip') and j_dst_ip == dst_packet.get('src_ip') and dst_packet.get('protocol') == 'UDP':
                        dst_packet_c1_stt = dst_packet.get('stt')
                        break
                if int(stt2) == int(dst_packet_c1_stt):
                    score += 1
                if int(success2) == 0:
                    score += 1
                print('c1, c2')

            #c3
            

            # c4
            if j_protocol == 'TCP' and j_dst_ip == '202.191.56.66':
                strpayload = "414c49434527532041" # ALICE'S A
                if strpayload in j_payload:
                    if int(stt4) == j_stt:
                        score += 1
                    if souIP4 == j_src_ip:    
                        score += 1
                    if desIP4 == '202.191.56.66':
                        score += 1
                    if int(souPort4) == j_src_port:
                        score += 1
                    if int(desPort4) == j_dst_port:
                        score += 1
                    if int(seq4) == j_seq:
                        score += 1
                    if int(ack4) == 1:
                        score += 1
                    if int(lenghttcp4) == 20:
                        score += 1
                    if int(lenghtdata4) == j_lenght_payload:
                        score += 1
                    if flag4 == 'ACK':
                        score += 1
                    if int(floor4) == 4:
                        score += 1
                    print('c4')
                    start_stt4 = j_stt
                    start_ack5 = j_seq

            # c5
            if j_stt > start_stt4 and start_stt5:
                if j_src_ip == '202.191.56.66' and j_protocol == 'TCP':
                    print(j_stt)
                    start_stt5 = False
                    if int(stt5) == j_stt:
                        score += 1
                    if souIP5 == j_src_ip:    
                        score += 1
                    if desIP5 == j_dst_ip:
                        score += 1
                    if int(souPort5) == j_src_port:
                        score += 1
                    if int(desPort5) == j_dst_port:
                        score += 1
                    if int(seq5) == j_seq:
                        score += 1
                    if int(ack5) == start_ack5:
                        score += 1
                    if int(lenghttcp5) == 20:
                        score += 1
                    if int(lenghtdata5) == 0:
                        score += 1
                    if flag5 == 'ACK':
                        score += 1
                    if int(success5) == 1:
                        score += 1
                    
            # c6
            if j_stt > start_stt4 and start_stt6:
                if j_dst_ip == '202.191.56.66' and j_protocol == 'TCP':
                    print(j_stt)
                    start_stt6 = False
                    if int(seq6) == j_seq:
                        score += 0.25
            
            # c7
            if j_stt > start_stt4 and start_stt7:
                if j_fin == 1:
                    print(j_stt)
                    start_stt7 = False
                    if int(stt7) == j_stt:
                        score += 0.25
                    if nhiphan7 == '000000010001':
                        score += 0.25
                    if ('FIN' in flag7) and ('ACK' in flag7):
                        score += 0.25
                    if int(seq7) == j_seq:
                        score += 0.25
                    
                    if int(lenghtdata7) == 0:
                        score += 0.25

        # Lưu submission

        submission, created = Submission.objects.get_or_create(
            assignment=assignment, student=student,
            defaults={'answers': json.dumps(answers), 'score': score, 'is_submitted': True}
        )
        if not created:
            submission.answers = json.dumps(answers)
            submission.score = score
            submission.is_submitted = True
            submission.save()

        return redirect('view_result', assignment_id=assignment.id)

def print_timestamp(ts, resol):
    # chuyển thời gian thành đơn vị giây
    ts_sec = ts // resol
    # phần sau dấu phẩy của giây
    ts_sec_resol = ts % resol
    # chuyển thời gian thành đơn vị tự định dạng
    ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts_sec))
    # trả về 1 chuỗi string
    return '{}.{}'.format(ts_str, ts_sec_resol)

def upload_pcap(request, assignment_id):
    # login_url = '/login/'
    # def get(self, request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
        # form = UploadFileForm(request.POST, request.FILES)
        # return render(request, 'apps/student/upload_pcap.html', {'form': form, 'assignment': assignment})
    
    if request.method == 'POST':
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
        
        start_time = None
        end_time = None

        first_pkt_timestamp = None
        first_pkt_timestamp_resolution = None

        last_pkt_timestamp = None
        last_pkt_timestamp_resolution = None

        connection_found1 = False
        connection_found2 = False
        total_data_bytes = 0

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

                fin = 0                
                if 'F' in tcp_pkt.flags:
                    fin = 1

                print(tcp_pkt.flags)

                start_file = '414c49434527532041'
                end_file = '454e440d'
                bps = 0
                if tcp_payload is not None and ip_pkt.dst == '202.191.56.66':
                    pkt_timestamp = (pkt_metadata.tshigh << 32 | pkt_metadata.tslow)
                    pkt_timestamp_resolution = pkt_metadata.tsresol
                    payload_hex = binascii.hexlify(tcp_payload).decode('utf-8')
                    if start_file in payload_hex:
                        first_pkt_timestamp = pkt_timestamp
                        first_pkt_timestamp_resolution = pkt_timestamp_resolution
                        connection_found1 = True

                    if connection_found1:    
                        last_pkt_timestamp = pkt_timestamp
                        last_pkt_timestamp_resolution = pkt_timestamp_resolution
                        total_data_bytes += len(tcp_payload)

                    if end_file in payload_hex:
                        connection_found1 = False
                        connection_found2 = True

                    if first_pkt_timestamp is not None and last_pkt_timestamp is not None and connection_found2:
                        first_ts_str = print_timestamp(first_pkt_timestamp, first_pkt_timestamp_resolution)
                        last_ts_str = print_timestamp(last_pkt_timestamp, last_pkt_timestamp_resolution)
                        time_diff = (last_pkt_timestamp - first_pkt_timestamp) / last_pkt_timestamp_resolution
                        bps = total_data_bytes / time_diff
                        bps = round(bps, 2)
                        print(bps)

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
                    'lenght_payload': len(tcp_pkt.payload),
                    'fin': fin,
                    'bps': bps
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
                    'lenght_payload': 0,
                    'fin': -1,
                    'bps': 0,
                }     
            else:
                continue
            
            data_list.append(packet_info)
        
        json_file_path = os.path.join(settings.BASE_DIR, 'data', 'pcap_data.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(data_list, json_file)

        Submission.objects.create(
            assignment_id=assignment,
            student=request.user,
            is_submitted=True
        )

        return redirect('ex4', assignment_id=assignment.id)
    else:
        form = UploadFileForm(request.POST, request.FILES)
        return render(request, 'apps/student/upload_pcap.html', {'form': form, 'assignment': assignment})
    
        

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


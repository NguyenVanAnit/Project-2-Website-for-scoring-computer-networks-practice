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
from scapy.all import DNS

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
        
@decorators.login_required(login_url = '/login/')
def get_home_teacher(request):
    return render(request, 'apps/teacher/home.html')

@decorators.login_required(login_url = '/login/')
def teacher_home(request):
    if request.user.role != 1:  # Check if the user is not a teacher
        return redirect('home')  # Redirect to a suitable page if the user is not a teacher
    return render(request, 'apps/teacher/home.html')

@decorators.login_required(login_url = '/login/')
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

# học sinh rời khỏi lớp
@decorators.login_required(login_url = '/login/')
def delete_class_for_student(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)
    student = request.user

    if student in class_instance.students.all():
        class_instance.students.remove(student)
        messages.success(request, f'Bạn đã rời khỏi lớp {class_instance.name} thành công.')
    else:
        messages.error(request, 'Bạn không thuộc lớp này.')

    return redirect('student_classes')

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
@decorators.login_required(login_url = '/login/')
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

@decorators.login_required(login_url = '/login/')
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
@decorators.login_required(login_url = '/login/')
def student_submission_detail(request, student_id):
    student = get_object_or_404(User, id=student_id)
    submissions = Submission.objects.filter(student=student)
    return render(request, 'apps/teacher/student_submission_detail.html', {'student': student, 'submissions': submissions})


@decorators.login_required(login_url = '/login/')
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
@decorators.login_required(login_url = '/login/')
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

@decorators.login_required(login_url = '/login/')
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submission = Submission.objects.filter(assignment_id=assignment, student=request.user).first()
    can_view_score = submission.is_submited if submission else False  # Assuming is_submited is True when the score is available

    return render(request, 'apps/student/assignment_detail.html', {
        'assignment': assignment,
        'submission': submission,
        'can_view_score': can_view_score
    })

class ViewResult(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, assignment_id):
        assignment = get_object_or_404(Assignment, id=assignment_id)
        submission = get_object_or_404(Submission, assignment=assignment, student=request.user)
        is_past_deadline = timezone.now() > assignment.deadline
        return render(request, 'apps/student/view_result.html', {
            'assignment': assignment,
            'submission': submission,
            'is_past_deadline': is_past_deadline
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

@decorators.login_required(login_url = '/login/')
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

        #c3
        souIP3 = request.POST.get('souIP3')
        desIP3 = request.POST.get('desIP3')
        souPort3 = request.POST.get('souPort3')
        desPort3 = request.POST.get('desPort3')
        
        stt31 = int(request.POST.get('stt31') or -1)
        nhiphan31 = request.POST.get('nhiphan31')
        flag31 = request.POST.get('flag31')
        seq31 = int(request.POST.get('seq31') or -1)
        ack31 = int(request.POST.get('ack31') or -1)
        lenghtdata31 = int(request.POST.get('lenghtdata31') or -1)

        stt32 = int(request.POST.get('stt32') or -1)
        nhiphan32 = request.POST.get('nhiphan32')
        flag32 = request.POST.get('flag32')
        seq32 = int(request.POST.get('seq32') or -1)
        ack32 = int(request.POST.get('ack32') or -1)
        lenghtdata32 = int(request.POST.get('lenghtdata32') or -1)

        stt33 = int(request.POST.get('stt33') or -1)
        nhiphan33 = request.POST.get('nhiphan33')
        flag33 = request.POST.get('flag33')
        seq33 = int(request.POST.get('seq33') or -1)
        ack33 = int(request.POST.get('ack33') or -1)
        lenghtdata33 = int(request.POST.get('lenghtdata33') or -1)

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

        #c8
        bps8 = (request.POST.get('bps8') or -111)

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
        start_syn3 = True
        start_synack3 = True
        start_ack3 = True
        start_stt4 = 99999999
        start_stt5 = True
        start_ack5 = -98989898
        start_stt6 = True
        start_stt7 = True
        max_bps = 0

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
            j_bps = packet.get('bps')
            j_syn = packet.get('syn')
            
            # c1, c2  
            if int(stt) == j_stt and j_protocol == 'UDP':
                # c1
                if souIP == j_src_ip:
                    souIP += '✔'
                    score += 0.2
                if desIP == j_dst_ip:
                    desIP += '✔'
                    score += 0.2
                if int(souPort) == j_src_port:
                    souPort += '✔'
                    score += 0.2
                if int(desPort) == j_dst_port:
                    desPort += '✔'
                    score += 0.2
                if int(floor) == 4:
                    floor += '✔'
                    score += 0.2

                # c2
                dst_packet_c1_stt = 0
                for dst_packet in packets:
                    if int(dst_packet.get('stt')) < int(stt):
                        continue
                    if j_src_ip == dst_packet.get('dst_ip') and j_dst_ip == dst_packet.get('src_ip') and dst_packet.get('protocol') == 'UDP':
                        dst_packet_c1_stt = dst_packet.get('stt')
                        break
                if int(stt2) == int(dst_packet_c1_stt):
                    stt2 += '✔'
                    score += 0.25
                if int(success2) == 0:
                    success2 += '✔'
                    score += 0.25

            #c3
            if j_protocol == 'TCP' and j_dst_ip == '202.191.56.66' and start_syn3 and j_syn == 1:
                start_syn3 = False
                if souIP3 == j_src_ip:
                    souIP3 += '✔'
                    score += 0.25
                if desIP3 == '202.191.56.66':
                    desIP3 += '✔'
                    score += 0.25
                if souPort3 == j_src_port:
                    souPort3 += '✔'
                    score += 0.25
                if desPort3 == j_dst_port:
                    desPort3 += '✔'
                    score += 0.25
                if stt31 == j_stt and nhiphan31 == '000000000010' and flag31 == 'SYN' and seq31 == j_seq and ack31 == 0 and lenghtdata31 == 0:
                    stt31 += '✔'
                    score += 0.5
                
            if j_protocol == 'TCP' and j_src_ip == '202.191.56.66' and start_synack3 and j_syn == 2:
                start_synack3 = False
                if stt32 == j_stt and nhiphan32 == '000000010010' and 'SYN' in flag32 and 'ACK' in flag32 and seq32 == j_seq and ack32 == 1 and lenghtdata32 == 0:
                    score += 0.5
                    stt32 += '✔'
            
            if j_protocol == 'TCP' and j_dst_ip == '202.191.56.66' and start_ack3 and (not start_synack3):
                start_ack3 = False
                if stt33 == j_stt and nhiphan33 == '000000000010' and flag33 == 'ACK' and seq33 == j_seq and ack32 == 1 and lenghtdata33 == 0:
                    score += 0.5
                    stt33 += '✔'

            # c4
            if j_protocol == 'TCP' and j_dst_ip == '202.191.56.66':
                strpayload = "414c49434527532041" # ALICE'S A
                if strpayload in j_payload:
                    if int(stt4) == j_stt:
                        stt4 += '✔'
                        score += 0.2
                    if souIP4 == j_src_ip:   
                        souIP4 += '✔' 
                        score += 0.1
                    if desIP4 == '202.191.56.66':
                        desIP4 += '✔'
                        score += 0.1
                    if int(souPort4) == j_src_port:
                        souPort4 += '✔'
                        score += 0.2
                    if int(desPort4) == j_dst_port:
                        desPort4 += '✔'
                        score += 0.2
                    if int(seq4) == j_seq:
                        seq4 += '✔'
                        score += 0.2
                    if int(ack4) == 1:
                        ack4 += '✔'
                        score += 0.2
                    if int(lenghttcp4) == 20:
                        lenghttcp4 += '✔'
                        score += 0.2
                    if int(lenghtdata4) == j_lenght_payload:
                        lenghtdata4 += '✔'
                        score += 0.2
                    if flag4 == 'ACK':
                        flag4 += '✔'
                        score += 0.2
                    if int(floor4) == 4:
                        floor4 += '✔'
                        score += 0.2
                    
                    start_stt4 = j_stt
                    start_ack5 = j_seq

            # c5
            if j_stt > start_stt4 and start_stt5:
                if j_src_ip == '202.191.56.66' and j_protocol == 'TCP':
                    print(j_stt)
                    start_stt5 = False
                    if int(stt5) == j_stt:
                        stt5 += '✔'
                        score += 0.2
                    if souIP5 == j_src_ip:    
                        souIP5 += '✔'
                        score += 0.1
                    if desIP5 == j_dst_ip:
                        desIP5 += '✔'
                        score += 0.1
                    if int(souPort5) == j_src_port:
                        souPort5 += '✔'
                        score += 0.2
                    if int(desPort5) == j_dst_port:
                        desPort5 += '✔'
                        score += 0.2
                    if int(seq5) == j_seq:
                        seq5 += '✔'
                        score += 0.2
                    if int(ack5) == start_ack5:
                        ack5 += '✔'
                        score += 0.2
                    if int(lenghttcp5) == 20:
                        lenghttcp5 += '✔'
                        score += 0.2
                    if int(lenghtdata5) == 0:
                        lenghtdata5 += '✔'
                        score += 0.2
                    if flag5 == 'ACK':
                        flag5 += '✔'
                        score += 0.2
                    if int(success5) == 1:
                        success5 += '✔'
                        score += 0.2
                    
            # c6
            if j_stt > start_stt4 and start_stt6:
                if j_dst_ip == '202.191.56.66' and j_protocol == 'TCP':
                    print(j_stt)
                    start_stt6 = False
                    if int(seq6) == j_seq:
                        seq6 += '✔'
                        score += 1
            
            # c7
            if j_stt > start_stt4 and start_stt7:
                if j_fin == 1:
                    print(j_stt)
                    start_stt7 = False
                    if int(stt7) == j_stt:
                        stt7 += '✔'
                        score += 0.2
                    if nhiphan7 == '000000010001':
                        nhiphan7 += '✔'
                        score += 0.2
                    if ('FIN' in flag7) and ('ACK' in flag7):
                        flag7 += '✔'
                        score += 0.2
                    if int(seq7) == j_seq:
                        seq7 += '✔'
                        score += 0.2
                    
                    if int(lenghtdata7) == 0:
                        lenghtdata7 += '✔'
                        score += 0.2

            #8
            if j_bps > max_bps:
                max_bps = j_bps
            if max_bps == bps8:
                bp8 += '✔'
                score += 0.5

        # Lưu submission

        # submission, created = Submission.objects.get_or_create(
        #     assignment=assignment, student=student,
        #     defaults={'answers': json.dumps(answers), 'score': score, 'is_submitted': True}
        # )
        # if not created:
        #     submission.answers = json.dumps(answers)
        #     submission.score = score
        #     submission.is_submitted = True
        #     submission.save()
        if stt == -1:
            stt = ''
        if souPort == -1:
            souPort = ''
        if desPort == -1:
            desPort = ''
        if floor == -1:
            floor = ''
        if stt2 == -1:
            stt2 = ''
        if success2 == -1:
            success2 = ''
        if souPort3 == -1:
            souPort3 = ''
        if desPort3 == -1:
            desPort3 = ''
        if stt31 == -1:
            stt31 = ''
        
        if seq31 == -1:
            seq31 = ''
        if ack31 == -1:
            ack31 = ''
        if lenghtdata31 == -1:
            lenghtdata31 = ''
        if stt32 == -1:
            stt32 = ''
        if nhiphan32 == -1:
            nhiphan32 = ''
        
        if seq32 == -1:
            seq32 = ''
        if ack32 == -1:
            ack32 = ''
        if lenghtdata32 == -1:
            lenghtdata32 = ''
        if stt33 == -1:
            stt33 = ''
        
        if seq33 == -1:
            seq33 = ''
        if ack33 == -1:
            ack33 = ''
        if lenghtdata33 == -1:
            lenghtdata33 = ''
        if stt4 == -1:
            stt4 = ''
        
        if souPort4 == -1:
            souPort4 = ''
        if desPort4 == -1:
            desPort4 = ''

        if seq4 == -1:
            seq4 = ''
        if ack4 == -1:
            ack4 = ''
        if lenghttcp4 == -1:
            lenghttcp4 = ''
        if lenghtdata4 == -1:
            lenghtdata4 = ''
        
        if floor4 == -1:
            floor4 = ''
        if success5 == -1:
            success5 = ''
        if seq6 == -1:
            seq6 = ''
        if stt7 == -1:
            stt7 = ''
        
        if seq7 == -1:
            seq7 = ''
        if ack7 == -1:
            ack7 = ''
        if lenghtdata7 == -1:
            lenghtdata7 = ''
        if bps8 == -111:
            bps8 = ''
        
        answers = {
            '1.Số thứ tự gói tin': stt,
            '1.Địa chỉ IP nguồn': souIP,
            '1.Địa chỉ IP đích': desIP,
            '1.Cổng nguồn': souPort,
            '1.Cổng đích': desPort,
            '1.Tầng': floor,
            '2.Số thứ tự gói tin': stt2,
            '2.Lý do': request.POST.get('reason21'),
            '2.Thành công hay không?': success2,
            '2.Lý do 2': request.POST.get('reason22'),
            '3.Địa chỉ IP nguồn': souIP3,
            '3.Địa chỉ IP đích': desIP3,
            '3.Cổng nguồn': souPort3,
            '3.Cổng đích': desPort3,
            '3.1.Số thứ tự gói tin': stt31,
            '3.1.Giá trị nhị phân trường Flag': nhiphan31,
            '3.1.Các cờ thiết lập': flag31,
            '3.1.Sequence number': seq31,
            '3.1.Ack number': ack31,
            '3.1.Kích thước phần dữ liệu': lenghtdata31,
            '3.2.Số thứ tự gói tin': stt32,
            '3.2.Giá trị nhị phân trường Flag': nhiphan32,
            '3.2.Các cờ thiết lập': flag32,
            '3.2.Sequence number': seq32,
            '3.2.Ack number': ack32,
            '3.2.Kích thước phần dữ liệu': lenghtdata32,
            '3.3.Số thứ tự gói tin': stt33,
            '3.3.Giá trị nhị phân trường Flag': nhiphan33,
            '3.3.Các cờ thiết lập': flag33,
            '3.3.Sequence number': seq33,
            '3.3.Ack number': ack33,
            '3.3.Kích thước phần dữ liệu': lenghtdata33,
            '4.Số thứ tự gói tin': stt4,
            '4.Địa chỉ IP nguồn': souIP4,
            '4.Địa chỉ IP đích': desIP4,
            '4.Cổng nguồn': souPort4,
            '4.Cổng đích': desPort4,
            '4.Sequence number': seq4,
            '4.Ack number': ack4,
            '4.Kích thước phần tiêu đề': lenghttcp4,
            '4.Kích thước phần dữ liệu': lenghtdata4,
            '4.Các cờ thiết lập': flag4,
            '4.Tầng mạng': floor4,
            '5.Số thứ tự gói tin': stt4,
            '5.Địa chỉ IP nguồn': souIP4,
            '5.Địa chỉ IP đích': desIP4,
            '5.Cổng nguồn': souPort4,
            '5.Cổng đích': desPort4,
            '5.Sequence number': seq4,
            '5.Ack number': ack4,
            '5.Kích thước phần tiêu đề': lenghttcp4,
            '5.Kích thước phần dữ liệu': lenghtdata4,
            '5 .Các cờ thiết lập': flag4,
            '5.Kết luận': success5,
            '5.Lý do': request.POST.get('reason5'),
            '6.Sequence number': seq6,
            '7.Số thứ tự gói tin': stt7,
            '7.Giá trị nhị phân trường Flag': nhiphan7,
            '7.Các cờ thiết lập': flag7,
            '7.Sequence number': seq7,
            '7.Ack number': ack7,
            '7.Kích thước phần dữ liệu': lenghtdata7,
            '8.Thông lượng trung bình': bps8
        }

        # return redirect('view_result', assignment_id=assignment.id)
        submission, created = Submission.objects.get_or_create(
            assignment=assignment, student=student,
            defaults={'answers': answers, 'score': score, 'is_submitted': True}
        )
        if not created:
            submission.answers = answers
            submission.score = score
            submission.is_submitted = True
            submission.save()
        print(score)
        return redirect('view_result', assignment_id=assignment.id)
    
class submitEx5(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request, assignment_id):
        assignment = get_object_or_404(Assignment, id=assignment_id)
        return render(request, 'apps/student/ex5.html', {'assignment': assignment})
    
    def post(self, request, assignment_id):
        assignment = get_object_or_404(Assignment, id=assignment_id)

        student = request.user

        current_time = timezone.now()

        #c1
        stt = int(request.POST.get('stt') or -1)
        protocol = request.POST.get('protocol')
        souIP = request.POST.get('souIP')
        desIP = request.POST.get('desIP')
        souPort = int(request.POST.get('souPort') or -1)
        desPort = int(request.POST.get('desPort') or -1)
        type1 = request.POST.get('type1')
        port1 = request.POST.get('port1')

        #c2
        stt2 = int(request.POST.get('stt2') or -1)
        protocol2 = request.POST.get('protocol2')
        souIP2 = request.POST.get('souIP2')
        desIP2 = request.POST.get('desIP2')
        souPort2 = int(request.POST.get('souPort2') or -1)
        desPort2 = int(request.POST.get('desPort2') or -1)
        type2 = request.POST.get('type2')
        mien2 = request.POST.get('mien2')
        mienIP2 = request.POST.get('mienIP2')

        #c3
        mien3 = request.POST.get('mien3')
        mienIP3 = request.POST.get('mienIP3')

        #c4
        stt41 = request.POST.get('stt41')
        stt42 = request.POST.get('stt42')
        stt43 = request.POST.get('stt43')
        port41a = int(request.POST.get('port41a') or -1)
        port41b = int(request.POST.get('port41b') or -1)
        port42 = request.POST.get('port42')

        #c5
        thongdiep5 = request.POST.get('thongdiep5')

        #c6
        protocol6 = request.POST.get('protocol6')
        port6 = int(request.POST.get('port6') or -1)
        phienban6 = request.POST.get('phienban6')
        truong6 = request.POST.get('truong6')

        #c7
        phienban7 = request.POST.get('phienban7')
        truong7 = request.POST.get('truong7')                    
        data7 = request.POST.get('data7')
        length7 = int(request.POST.get('lenght7') or -1)
        goi7 = int(request.POST.get('goi7') or -1)

        #c8
        mien8 = request.POST.get('mien8')
        mienIP8 = request.POST.get('mienIP8')
        truong8 = request.POST.get('truong8')

        with open('data/pcap_data.json', 'r') as json_file:
            packets = json.load(json_file)

        score = 0
        start2 = False
        start_syn3 = True
        start_synack3 = True
        start_ack3 = True

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
            j_bps = packet.get('bps')
            j_syn = packet.get('syn')
            j_dns = packet.get('dns')

            #c1
            if stt == j_stt and j_dns == '1':
                start2 = True
                if protocol == 'UDP':
                    protocol += '✔'
                    score += 0.1
                if souIP == j_src_ip:
                    souIP += '✔'
                    score += 0.1
                if desIP == j_dst_ip:
                    score += 0.1
                    desIP += '✔'
                if souPort == j_src_port:
                    score += 0.1
                    souPort += '✔'
                if desPort == j_dst_port:
                    score += 0.1
                    desPort += '✔'
                if port1 == 'DNS':
                    port1 += '✔'
                    score += 0.1
                if type1 == 'A':
                    score += 0.1
                    type1 += '✔'

            #c2
            if j_src_ip == '1.1.1.1' and start2 and j_dns == '1':
                start2 = False
                if stt2 == j_stt:
                    stt2 += '✔'
                    score += 0.1
                if protocol2 == 'UDP':
                    protocol2 += '✔'
                    score += 0.1
                if souIP2 == j_src_ip:
                    souIP2 += '✔'
                    score += 0.1
                if desIP2 == j_dst_ip:
                    desIP2 += '✔'
                    score += 0.1
                if souPort2 == j_src_port:
                    souPort2 += '✔'
                    score += 0.1
                if desPort2 == j_dst_port:
                    desPort2 += '✔'
                    score += 0.1
                if type2 == 'A':
                    type2 += '✔'
                    score += 0.1
                if mien2 == 'nct.soict.hust.edu.vn':
                    mien2 += '✔'
                    score += 0.1
                if mienIP2 == '202.191.56.66':
                    mienIP2 += '✔'
                    score += 0.1

            #c3
            if 'lingosolution.co.uk' in mien3:
                mien3 += '✔'
                score += 0.3
            if mienIP3 == '149.255.58.41':
                mienIP3 += '✔'
                score += 0.4

            #c4
            if j_protocol == 'TCP' and j_dst_ip == '202.191.56.66' and start_syn3 and j_syn == 1:
                start_syn3 = False
                if stt41 == j_stt:
                    stt41 += '✔'
                    score += 0.2
                if port41a == j_src_ip:
                    port41a += '✔'
                    score += 0.2
                if port41b == j_dst_ip:
                    score += 0.2
                    port41b += '✔'
            
            if port42 == 'HTTP':
                port42 += '✔'
                score += 0.2

            if j_protocol == 'TCP' and j_src_ip == '202.191.56.66' and start_synack3 and j_syn == 2:
                start_synack3 = False
                if stt42 == j_stt:
                    stt42 += '✔'
                    score += 0.2
            
            if j_protocol == 'TCP' and j_dst_ip == '202.191.56.66' and start_ack3 and (not start_synack3):
                start_ack3 = False
                if stt43 == j_stt:
                    stt43 += '✔'
                    score += 0.2
            
            #c5

            #c6
            if protocol6 == 'TCP':
                protocol6 += '✔'
                score += 0.2
            if port6 == 80:
                port6 += '✔'
                score += 0.2
            if 'HTTP' in phienban6 and '1.1' in phienban6:
                score += 0.2
                phienban6 += '✔'
            if 'keep-alive' in truong6:
                score += 0.2
                truong6 += '✔'

            #c7
            if 'HTTP' in phienban7 and '1.1' in phienban7:
                score += 0.2
                phienban7 += '✔'
            if 'keep-alive' in truong7:
                score += 0.2
                truong7 += '✔'
            if 'text/html' in data7:
                score += 0.2
                data7 += '✔'
            if length7 == j_lenght_payload:
                score += 0.2
                length7 += '✔'
            if goi7 == 16:
                score += 0.2
                goi7 += '✔'

            #c8
            if 'lingosolution.co.uk' in mien8:
                score += 0.2
                mien8 += '✔'
            if mienIP8 == '149.255.58.41':
                score += 0.2
                mienIP8 += '✔'
            if truong8 == 'http://nct.soict.hust.edu.vn/':
                score += 0.2
                truong8 += '✔'

        if stt == -1:
            stt = ''
        if stt2 == -1:
            stt2 = ''
        if souPort == -1:
            souPort = ''
        if desPort == -1:
            desPort = ''
        if souPort2 == -1:
            souPort2 = ''
        if desPort2 == -1:
            desPort2 = ''
        if port41a == -1:
            port41a = ''
        if port41b == -1:
            port41b = ''
        if port6 == -1:
            port6 = ''
        if length7 == -1:
            length7 = ''
        if goi7 == -1:
            goi7 = ''

        answers = {
            '1.Số thứ tự gói tin': stt,
            '1.Giao thức tầng giao vận': protocol,
            '1.Địa chỉ IP nguồn': souIP,
            '1.Địa chỉ IP đích': desIP,
            '1.Cổng nguồn': souPort,
            '1.Cổng đích': desPort,
            '1.Cổng dịch vụ': port1,
            '1.Kiểu thông tin truy vấn': type1,
            '1.Cho biết gửi đến nút mạng nào?': request.POST.get('reason12'),
            '2.Số thứ tự gói tin': stt2,
            '2.Giao thức tầng giao vận': protocol2,
            '2.Địa chỉ IP nguồn': souIP2,
            '2.Địa chỉ IP đích': desIP2,
            '2.Cổng nguồn': souPort2,
            '2.Cổng đích': desPort2,
            '2.Kiểu thông tin truy vấn': type2,
            '2.Tên miền được truy vấn': mien2,
            '2.Địa chỉ IP của tên miền được truy vấn': mienIP2,
            '2.Tại sao xác định được?': request.POST.get('reason2'),
            '3.Tên miền khác được truy vấn': mien3,
            '3.Địa chỉ IP của tên miền đó là': mienIP3,
            '3.Tại sao': request.POST.get('reason3'),
            '4.Số thứ tự gói 1(No)': stt41,
            '4.Số thứ tự gói 2(No)': stt42,
            '4.Số thứ tự gói 3(No)': stt43,
            '4.Web Browser': port41a,
            '4.Web Server': port41b,
            '4.Cổng ứng dụng của dịch vụ nào?': port42,
            '5.Những thông điệp nào được gửi đi liên tiếp mà không đợi thông điệp trả lời?': request.POST.get('thongdiep5'),
            '5.Tại sao?': request.POST.get('reason5'),
            '6.Giao thức tầng giao vận': protocol6,
            '6.Số hiệu cổng ứng dụng đích': port6,
            '6.Phiên bản của giao thức HTTP': phienban6,
            '6.Connection': truong6,
            '7.Phiên bản của giao thức HTTP': phienban7,
            '7.Connection': truong7,
            '7.Phần thân chứa dữ liệu': data7,
            '7.Dữ liệu này có kích thước': length7,
            '7.Bao nhiêu gói tin TCP': goi7,
            '7.Còn duy trì không?': request.POST.get('reason7'),
            '8.Tên miền': mien8,
            '8.Địa chỉ IP': mienIP8,
            '8.Tại sao:': request.POST.get('reason8'),
            '8.Referer': truong8,
            '9.Điền đoạn văn': request.POST.get('thieu9')
        }

        # return redirect('view_result', assignment_id=assignment.id)
        submission, created = Submission.objects.get_or_create(
            assignment=assignment, student=student,
            defaults={'answers': answers, 'score': score, 'is_submitted': True}
        )
        if not created:
            submission.answers = answers
            submission.score = score
            submission.is_submitted = True
            submission.save()
        print(score)
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

        dns_number = 0

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

            if ip_pkt.haslayer(DNS):
                dns_number = 1

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

                syn = 0
                if tcp_pkt.flags == 'S':
                    syn = 1
                elif tcp_pkt.flags == 'SA':
                    syn = 2


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
                    'bps': bps,
                    'syn': syn,
                    'dns': dns_number
                }
                dns_number = 0
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
                    'syn': -1,
                    'dns': dns_number
                }     
                dns_number = 0
            else:
                continue
            
            data_list.append(packet_info)
        
        json_file_path = os.path.join(settings.BASE_DIR, 'data', 'pcap_data.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(data_list, json_file)

        Submission.objects.create(
            assignment_id=assignment.id,
            student=request.user,
            is_submitted=True
        )
        if assignment.role == 1:
            return redirect('ex5', assignment_id=assignment.id)
        else:
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


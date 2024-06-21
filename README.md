# Giới thiệu
- Trang web hỗ trợ quản lý sinh viên, quản lý lớp học, quản lý bài thi, được tạo ra để hỗ trợ chấm điểm tự động thực hành môn Mạng Máy Tính của ĐH Bách Khoa Hà Nội.
- Bằng cách phân tích dữ liệu file pcap, chuyển dữ liệu sang file JSON để tối ưu dung lượng, so sánh và đưa ra kết quả bài thực hành.
# Hướng dẫn cài đặt
- Cài đặt Python
#
    pip install django
- Cài đặt thư viện Django
#
    pip install scapy
- Cài đặt thư viện Scapy
#
    ROLE_CHOICES = (
        (0, 'Học sinh'),
        (1, 'Giáo viên'),
        (2, 'Quản trị viên'),
    )
    role = models.IntegerField(choices=ROLE_CHOICES, default=1)
    user_id = models.IntegerField(unique=True, default=13)
- Truy cập AbstractUser để thêm đoạn code sau
#
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), blank=True)
    # sửa
    ROLE_CHOICES = (
        (0, 'Học sinh'),
        (1, 'Giáo viên'),
        (2, 'Quản trị viên'),
    )
    role = models.IntegerField(choices=ROLE_CHOICES, default=1)
    user_id = models.IntegerField(unique=True, default=13)
    # 
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
- Tổng quan code sau khi thêm
#
    python manage.py runserver 8003
- Truy cập webproject2 để chạy lệnh trên khởi động chương trình
# Sử dụng tài khoản đã tạo trước
- SINH VIÊN
- username: student1 - password: annguyen
- username: student2 - password: annguyen
- GIẢNG VIÊN
- username: teacher1 - password: annguyen
- username: teacher2 - password: annguyen
# Hướng dẫn tạo tài khoản mới
    python manage.py createsuperuser
- Chạy lệnh trên, nhập username và password tạo tài khoản admin
- Truy cập http://localhost:8003/admin/
- Đăng nhập bằng tài khoản admin, sử dụng chức năng tạo tài khoản
- Khi tạo tài khoản, chú ý thay đổi trường default ở role và user_id đã chỉnh sửa ở trên để tạo tài khoản cho giảng viên và sinh viên
#
    role = models.IntegerField(choices=ROLE_CHOICES, default=0)
    user_id = models.IntegerField(unique=True, default=20210001)
- Ví dụ, trước khi tạo tài khoản có user_id là 20210001 thì cần sửa như ví dụ trên.
# Cảm ơn đã ghé thăm sản phẩm, sản phẩm còn nhiều thiếu sót, hy vọng không ảnh hưởng đến bạn. 
